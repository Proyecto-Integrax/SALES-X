"""Concurrencia: dos usuarios actuando a la vez sobre el MISMO pedido no pueden violar la máquina de estados.

Requiere PostgreSQL (bloqueo de filas); se omite en SQLite. Ejecutar con TEST_DATABASE_URL (ver README).
"""

import re
import threading

import pytest
from fastapi.testclient import TestClient

from app.database import engine
from app.main import app
from app.services.pedidos import TRANSICIONES

API = "/api/v1"
RONDAS = 30

pytestmark = pytest.mark.skipif(engine.url.get_backend_name() == "sqlite", reason="requiere PostgreSQL (bloqueo de filas)")


def _en_preparacion(client, h, cliente_id, producto_id):
    body = {"cliente_id": cliente_id, "items": [{"producto_id": producto_id, "cantidad": 1}]}
    pid = client.post(f"{API}/pedidos", json=body, headers=h).json()["pedido_id"]
    for estado in ("Confirmado", "En preparación"):
        assert client.patch(f"{API}/pedidos/{pid}/estado", json={"estado": estado}, headers=h).status_code == 200
    return pid


def _carrera(acciones):
    """Lanza las acciones en hilos distintos y las libera a la vez."""
    barrera, resultados = threading.Barrier(len(acciones)), []

    def correr(f):
        barrera.wait()
        resultados.append(f(TestClient(app)))

    hilos = [threading.Thread(target=correr, args=(f,)) for f in acciones]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    return resultados


def _cadena_valida(auditoria, inicial):
    """Cada transición auditada debe partir del estado al que llegó la anterior y estar permitida."""
    actual = inicial
    for ev in auditoria:
        m = re.match(r"^(.+?) -> (.+?)(?:\.|$)", ev["descripcion"] or "")
        if ev["accion"] not in ("CAMBIO_ESTADO", "CANCELAR") or not m:
            continue
        origen, destino = m.group(1), m.group(2)
        if origen != actual or destino not in TRANSICIONES.get(origen, set()):
            return False, f"{origen} -> {destino} (el estado real era {actual})"
        actual = destino
    return True, actual


def test_enviar_y_cancelar_a_la_vez_no_rompen_la_maquina_de_estados(client, vendedor, cliente_id, producto):
    violaciones = []
    for ronda in range(RONDAS):
        pid = _en_preparacion(client, vendedor, cliente_id, producto["id"])
        res = _carrera([
            lambda c: c.patch(f"{API}/pedidos/{pid}/estado", json={"estado": "Enviado"}, headers=vendedor).status_code,
            lambda c: c.post(f"{API}/pedidos/{pid}/cancelar", json={"motivo": "cancelación simultánea"}, headers=vendedor).status_code,
        ])
        aud = client.get(f"{API}/pedidos/{pid}/auditoria", headers=vendedor).json()
        final = client.get(f"{API}/pedidos/{pid}", headers=vendedor).json()["estado"]
        ok, detalle = _cadena_valida(aud, "Pendiente")
        if not ok or detalle != final or sorted(res).count(200) != 1:
            violaciones.append((ronda, sorted(res), final, detalle))
    assert not violaciones, f"{len(violaciones)} de {RONDAS} rondas violaron la máquina de estados: {violaciones[:3]}"


def test_dos_cancelaciones_simultaneas_solo_una_prospera(client, vendedor, cliente_id, producto):
    for _ in range(RONDAS):
        pid = _en_preparacion(client, vendedor, cliente_id, producto["id"])
        res = _carrera([lambda c: c.post(f"{API}/pedidos/{pid}/cancelar", json={"motivo": "doble clic"}, headers=vendedor).status_code] * 2)
        aud = client.get(f"{API}/pedidos/{pid}/auditoria", headers=vendedor).json()
        assert sorted(res) == [200, 409], res
        assert [a["accion"] for a in aud].count("CANCELAR") == 1  # un solo registro de auditoría


def test_modificar_y_cancelar_a_la_vez_no_deja_un_pedido_cancelado_modificado(client, vendedor, cliente_id, producto):
    for _ in range(RONDAS):
        body = {"cliente_id": cliente_id, "items": [{"producto_id": producto["id"], "cantidad": 1}]}
        pid = client.post(f"{API}/pedidos", json=body, headers=vendedor).json()["pedido_id"]
        res = _carrera([
            lambda c: c.put(f"{API}/pedidos/{pid}", json={"descripcion": "cambio simultáneo"}, headers=vendedor).status_code,
            lambda c: c.post(f"{API}/pedidos/{pid}/cancelar", json={"motivo": "cancelación simultánea"}, headers=vendedor).status_code,
        ])
        aud = [a["accion"] for a in client.get(f"{API}/pedidos/{pid}/auditoria", headers=vendedor).json()]
        # Si la cancelación llegó primero, la modificación debe rechazarse (409) y no quedar auditada como MODIFICAR.
        if aud.index("CANCELAR") < (aud.index("MODIFICAR") if "MODIFICAR" in aud else 10**6):
            assert "MODIFICAR" not in aud[aud.index("CANCELAR"):], (res, aud)

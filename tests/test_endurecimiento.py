"""Pruebas de endurecimiento v1.1: REQ-14 (bloqueo en BD), REQ-15 (consumidores), REQ-16 (cookie+CSRF), REQ-17 (contraseñas)."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.main import app
from app.models import ConsumidorApi, IntentoLogin
from app.security import hash_api_key
from app.services import login_throttle

API = "/api/v1"
LOGIN = f"{API}/auth/login"


def web():
    """Cliente nuevo con su propio almacén de cookies (como un navegador)."""
    return TestClient(app)


def login(c, correo, password):
    return c.post(LOGIN, json={"correo": correo, "contrasena": password})


def crear_usuario(client, admin, password="Inicial2026x"):
    correo = f"u{uuid.uuid4().hex[:8]}@test.local"
    r = client.post(f"{API}/vendedores", headers=admin, json={"nombre": "Usuario Prueba", "correo": correo, "contrasena": password})
    assert r.status_code == 201, r.text
    return correo, r.json()


def csrf(c):
    return {"X-CSRF-Token": c.cookies.get("salesx_csrf")}


def usuario_con_clave_propia(client, admin, nueva="ClavePropia2026z"):
    correo, u = crear_usuario(client, admin)
    c = web()
    assert login(c, correo, "Inicial2026x").status_code == 200
    r = c.post(f"{API}/auth/cambiar-contrasena", json={"actual": "Inicial2026x", "nueva": nueva}, headers=csrf(c))
    assert r.status_code == 204, r.text
    return correo, nueva, u["vendedor_id"]


# ======================= REQ-14: bloqueo de login en la base de datos =======================
def test_fallos_de_login_quedan_en_la_bd_y_bloquean(client):
    correo = f"bd{uuid.uuid4().hex[:6]}@test.local"
    for _ in range(5):
        assert login(client, correo, "mala").status_code == 401
    with SessionLocal() as db:  # sesión distinta = otra "instancia": el bloqueo es compartido
        assert login_throttle.bloqueado(db, correo) is True
        assert db.scalar(select(func.count()).select_from(IntentoLogin).where(IntentoLogin.clave == correo)) == 5
    assert login(client, correo, "mala").status_code == 429


def test_login_correcto_borra_los_fallos(client, admin):
    correo, _ = crear_usuario(client, admin)
    for _ in range(3):
        login(client, correo, "incorrecta")
    assert login(client, correo, "Inicial2026x").status_code == 200
    client.cookies.clear()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(IntentoLogin).where(IntentoLogin.clave == correo)) == 0
        assert login_throttle.bloqueado(db, correo) is False


# ======================= REQ-15: claves por consumidor =======================
def test_consumidor_clave_se_muestra_una_vez_y_se_usa(client, admin, vendedor, cliente_id, producto):
    nombre = f"Sistema-{uuid.uuid4().hex[:6]}"
    r = client.post(f"{API}/consumidores", headers=admin, json={"nombre": nombre})
    assert r.status_code == 201, r.text
    clave = r.json()["clave"]
    assert clave.startswith("sx_") and len(clave) > 40

    listado = client.get(f"{API}/consumidores", headers=admin).json()
    assert all("clave" not in c and "clave_hash" not in c for c in listado)  # nunca se vuelve a exponer
    assert next(c for c in listado if c["nombre"] == nombre)["ultimo_uso"] is None

    body = {"cliente_id": cliente_id, "items": [{"producto_id": producto["id"], "cantidad": 1}]}
    pid = client.post(f"{API}/pedidos", json=body, headers=vendedor).json()["pedido_id"]
    H = {"X-API-Key": clave}
    assert client.get(f"{API}/integracion/pedidos/{pid}", headers=H).status_code == 200
    assert client.post(f"{API}/integracion/pedidos/{pid}/solicitudes", headers=H, json={"tipo": "modificacion", "detalle": "Cambiar cantidad"}).status_code == 202

    assert next(c for c in client.get(f"{API}/consumidores", headers=admin).json() if c["nombre"] == nombre)["ultimo_uso"] is not None
    aud = client.get(f"{API}/pedidos/{pid}/auditoria", headers=vendedor).json()
    assert f"consumidor: {nombre}" in aud[-1]["descripcion"]


def test_consumidor_desactivado_y_reactivado(client, admin):
    r = client.post(f"{API}/consumidores", headers=admin, json={"nombre": f"Temp-{uuid.uuid4().hex[:6]}"}).json()
    H = {"X-API-Key": r["clave"]}
    url = f"{API}/integracion/disponibilidad/{uuid.uuid4()}"
    assert client.get(url, headers=H).status_code == 404  # autenticada (el producto no existe)
    assert client.patch(f"{API}/consumidores/{r['consumidor_id']}", headers=admin, json={"activo": False}).status_code == 200
    assert client.get(url, headers=H).status_code == 401
    client.patch(f"{API}/consumidores/{r['consumidor_id']}", headers=admin, json={"activo": True})
    assert client.get(url, headers=H).status_code == 404


def test_consumidor_expirado_no_autentica(client):
    clave = "sx_clave-expirada-de-prueba"
    with SessionLocal() as db:
        db.add(ConsumidorApi(nombre=f"Exp-{uuid.uuid4().hex[:6]}", clave_hash=hash_api_key(clave), expira=datetime.now(timezone.utc) - timedelta(minutes=1)))
        db.commit()
    r = client.get(f"{API}/integracion/disponibilidad/{uuid.uuid4()}", headers={"X-API-Key": clave})
    assert r.status_code == 401


def test_consumidores_validaciones_y_permisos(client, admin, vendedor):
    assert client.get(f"{API}/consumidores", headers=vendedor).status_code == 403
    assert client.post(f"{API}/consumidores", headers=vendedor, json={"nombre": "Intruso"}).status_code == 403
    pasado = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    assert client.post(f"{API}/consumidores", headers=admin, json={"nombre": "Pasado", "expira": pasado}).status_code == 422
    n = f"Dup-{uuid.uuid4().hex[:6]}"
    assert client.post(f"{API}/consumidores", headers=admin, json={"nombre": n}).status_code == 201
    assert client.post(f"{API}/consumidores", headers=admin, json={"nombre": n}).status_code == 409
    assert client.patch(f"{API}/consumidores/{uuid.uuid4()}", headers=admin, json={"activo": False}).status_code == 404


def test_clave_invalida_da_mensaje_generico_y_existe_el_consumidor_inicial(client, admin):
    r = client.get(f"{API}/integracion/disponibilidad/{uuid.uuid4()}", headers={"X-API-Key": "sx_no-existe"})
    assert r.status_code == 401 and "inválida" in r.json()["detail"]
    assert any(c["nombre"] == "INTEGRAX-inicial" for c in client.get(f"{API}/consumidores", headers=admin).json())


# ======================= REQ-16: cookie HttpOnly + CSRF =======================
def test_login_fija_cookie_httponly_y_cookie_csrf_legible(client):
    c = web()
    r = login(c, "admin@test.local", "AdminTest2026*")
    cookies = r.headers.get_list("set-cookie")
    sesion = next(h for h in cookies if h.startswith("salesx_session=")).lower()
    token_csrf = next(h for h in cookies if h.startswith("salesx_csrf=")).lower()
    assert "httponly" in sesion and "samesite=strict" in sesion
    assert "httponly" not in token_csrf  # el JavaScript debe poder leerla para enviarla en la cabecera


def test_con_cookie_las_escrituras_exigen_csrf(client, cliente_id, producto):
    c = web()
    login(c, "vendedor@salesx.local", "Ventas2026*")
    assert c.get(f"{API}/auth/me").status_code == 200  # lectura por cookie, sin CSRF
    body = {"cliente_id": cliente_id, "items": [{"producto_id": producto["id"], "cantidad": 1}]}
    assert c.post(f"{API}/pedidos", json=body).status_code == 403  # sin cabecera
    assert c.post(f"{API}/pedidos", json=body, headers={"X-CSRF-Token": "incorrecto"}).status_code == 403
    assert c.post(f"{API}/pedidos", json=body, headers=csrf(c)).status_code == 201


def test_bearer_no_necesita_csrf(client, vendedor, cliente_id, producto):
    body = {"cliente_id": cliente_id, "items": [{"producto_id": producto["id"], "cantidad": 1}]}
    assert web().post(f"{API}/pedidos", json=body, headers=vendedor).status_code == 201


def test_logout_elimina_la_sesion(client):
    c = web()
    login(c, "admin@test.local", "AdminTest2026*")
    assert c.get(f"{API}/auth/me").status_code == 200
    assert c.post(f"{API}/auth/logout").status_code == 204
    assert c.get(f"{API}/auth/me").status_code == 401


# ======================= REQ-17: contraseñas =======================
def test_politica_de_contrasenas(client, admin):
    base = {"nombre": "Prueba Politica", "correo": "maria.gomez@test.local"}
    for mala in ["Corta1", "sololetrasaquitodo", "12345678901234", "Password123", "maria.gomez2026"]:
        r = client.post(f"{API}/vendedores", headers=admin, json={**base, "contrasena": mala})
        assert r.status_code == 422, f"debería rechazar {mala!r}"


def test_usuario_nuevo_debe_cambiar_su_contrasena(client, admin):
    correo, _ = crear_usuario(client, admin)
    c = web()
    assert login(c, correo, "Inicial2026x").status_code == 200
    assert c.get(f"{API}/auth/me").json()["debe_cambiar_contrasena"] is True
    assert c.get(f"{API}/pedidos").status_code == 403  # bloqueado hasta cambiarla
    assert c.get(f"{API}/catalogo/productos").status_code == 403

    cambiar = f"{API}/auth/cambiar-contrasena"
    assert c.post(cambiar, json={"actual": "Equivocada2026", "nueva": "NuevaClave2026z"}, headers=csrf(c)).status_code == 400
    assert c.post(cambiar, json={"actual": "Inicial2026x", "nueva": "Inicial2026x"}, headers=csrf(c)).status_code == 422
    assert c.post(cambiar, json={"actual": "Inicial2026x", "nueva": "debil"}, headers=csrf(c)).status_code == 422
    assert c.post(cambiar, json={"actual": "Inicial2026x", "nueva": "NuevaClave2026z"}, headers=csrf(c)).status_code == 204

    assert c.get(f"{API}/auth/me").json()["debe_cambiar_contrasena"] is False
    assert c.get(f"{API}/pedidos").status_code == 200
    assert login(web(), correo, "NuevaClave2026z").status_code == 200
    assert login(web(), correo, "Inicial2026x").status_code == 401


def test_admin_que_restablece_la_clave_obliga_a_cambiarla(client, admin):
    correo, nueva, vid = usuario_con_clave_propia(client, admin)
    c = web()
    login(c, correo, nueva)
    assert c.get(f"{API}/pedidos").status_code == 200
    r = client.patch(f"{API}/vendedores/{vid}", headers=admin, json={"contrasena": "Restablecida2026q"})
    assert r.status_code == 200 and r.json()["debe_cambiar_contrasena"] is True
    c2 = web()
    login(c2, correo, "Restablecida2026q")
    assert c2.get(f"{API}/pedidos").status_code == 403


def test_cambio_de_contrasena_tambien_se_bloquea_por_intentos(client, admin):
    correo, _ = crear_usuario(client, admin)
    c = web()
    login(c, correo, "Inicial2026x")
    for _ in range(5):
        assert c.post(f"{API}/auth/cambiar-contrasena", json={"actual": "Mala123456x", "nueva": "OtraClave2026z"}, headers=csrf(c)).status_code == 400
    assert c.post(f"{API}/auth/cambiar-contrasena", json={"actual": "Mala123456x", "nueva": "OtraClave2026z"}, headers=csrf(c)).status_code == 429

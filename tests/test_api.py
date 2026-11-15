"""Pruebas de integración de la API de SALES-X (trazables a RF/RNF/CU, ver docs/E6 y E7)."""

import uuid
from decimal import Decimal

API = "/api/v1"
KEY = {"X-API-Key": "api-key-de-pruebas"}


def nuevo_pedido(client, h, cliente_id, producto_id, cantidad=2, **extra):
    body = {"cliente_id": cliente_id, "items": [{"producto_id": producto_id, "cantidad": cantidad}], **extra}
    return client.post(f"{API}/pedidos", json=body, headers=h)


# ---------- Salud y autenticación (RNF-03, RNF-04) ----------
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["database"] == "ok"


def test_login_ok_y_me(client, vendedor):
    r = client.get(f"{API}/auth/me", headers=vendedor)
    assert r.status_code == 200 and r.json()["rol"] == "vendedor"
    assert "contrasena" not in r.json()


def test_login_incorrecto(client):
    r = client.post(f"{API}/auth/login", json={"correo": "vendedor@salesx.local", "contrasena": "mala"})
    assert r.status_code == 401


def test_endpoints_protegidos_sin_token(client):
    assert client.get(f"{API}/pedidos").status_code == 401
    assert client.get(f"{API}/reportes/ventas").status_code == 401
    assert client.get(f"{API}/catalogo/productos").status_code == 401


def test_token_manipulado(client):
    r = client.get(f"{API}/pedidos", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401


def test_bloqueo_por_intentos_fallidos(client):
    for _ in range(5):
        client.post(f"{API}/auth/login", json={"correo": "bloqueo@test.local", "contrasena": "x"})
    r = client.post(f"{API}/auth/login", json={"correo": "bloqueo@test.local", "contrasena": "x"})
    assert r.status_code == 429


def test_vendedor_no_administra_usuarios(client, vendedor):
    assert client.get(f"{API}/vendedores", headers=vendedor).status_code == 403


def test_admin_crea_usuario(client, admin):
    correo = f"nuevo{uuid.uuid4().hex[:6]}@test.local"
    r = client.post(f"{API}/vendedores", headers=admin, json={"nombre": "Nuevo Vendedor", "correo": correo, "contrasena": "Clave12345"})
    assert r.status_code == 201 and r.json()["rol"] == "vendedor"
    dup = client.post(f"{API}/vendedores", headers=admin, json={"nombre": "Otro", "correo": correo, "contrasena": "Clave12345"})
    assert dup.status_code == 409


# ---------- Catálogo / disponibilidad (RF-11) ----------
def test_catalogo_y_disponibilidad(client, vendedor, producto, agotado):
    assert len(client.get(f"{API}/catalogo/clientes", headers=vendedor).json()) >= 1
    prods = client.get(f"{API}/catalogo/productos", params={"q": "mouse"}, headers=vendedor).json()
    assert len(prods) == 1
    d = client.get(f"{API}/catalogo/productos/{producto['id']}/disponibilidad", headers=vendedor)
    assert d.status_code == 200 and d.json()["disponible"] > 0
    assert client.get(f"{API}/catalogo/productos/{agotado}/disponibilidad", headers=vendedor).json()["disponible"] == 0
    assert client.get(f"{API}/catalogo/productos/{uuid.uuid4()}/disponibilidad", headers=vendedor).status_code == 404


# ---------- Registrar pedido y cálculos (RF-01/02/03/07) ----------
def test_crear_pedido_calcula_totales(client, vendedor, cliente_id, producto):
    r = nuevo_pedido(client, vendedor, cliente_id, producto["id"], cantidad=3, descripcion="Pedido de prueba")
    assert r.status_code == 201, r.text
    p = r.json()
    sub = producto["precio"] * 3
    assert Decimal(p["subtotal"]) == sub
    assert Decimal(p["impuestos"]) == (sub * Decimal("0.19")).quantize(Decimal("0.01"))
    assert Decimal(p["total"]) == Decimal(p["subtotal"]) + Decimal(p["impuestos"])
    assert p["estado"] == "Pendiente" and len(p["detalles"]) == 1


def test_precio_se_toma_del_catalogo_no_del_cliente(client, vendedor, cliente_id, producto):
    body = {"cliente_id": cliente_id, "items": [{"producto_id": producto["id"], "cantidad": 1, "precio_unitario": "1"}]}
    p = client.post(f"{API}/pedidos", json=body, headers=vendedor).json()
    assert Decimal(p["detalles"][0]["precio_unitario"]) == producto["precio"]


def test_lineas_repetidas_se_consolidan(client, vendedor, cliente_id, producto):
    body = {"cliente_id": cliente_id, "items": [{"producto_id": producto["id"], "cantidad": 1}, {"producto_id": producto["id"], "cantidad": 4}]}
    p = client.post(f"{API}/pedidos", json=body, headers=vendedor).json()
    assert len(p["detalles"]) == 1 and p["detalles"][0]["cantidad"] == 5


def test_validaciones_de_entrada(client, vendedor, cliente_id, producto, agotado):
    assert nuevo_pedido(client, vendedor, cliente_id, producto["id"], cantidad=0).status_code == 422
    assert nuevo_pedido(client, vendedor, cliente_id, producto["id"], cantidad=-5).status_code == 422
    assert client.post(f"{API}/pedidos", json={"cliente_id": cliente_id, "items": []}, headers=vendedor).status_code == 422
    assert nuevo_pedido(client, vendedor, str(uuid.uuid4()), producto["id"]).status_code == 422  # cliente inexistente
    assert nuevo_pedido(client, vendedor, cliente_id, str(uuid.uuid4())).status_code == 422  # producto inexistente
    assert nuevo_pedido(client, vendedor, cliente_id, agotado, cantidad=1).status_code == 409  # sin disponibilidad
    assert nuevo_pedido(client, vendedor, cliente_id, producto["id"], cantidad=producto["disponible"] + 1).status_code == 409


# ---------- Consultar (RF-06 / RF-09) ----------
def test_consultar_y_filtrar(client, vendedor, cliente_id, producto):
    pid = nuevo_pedido(client, vendedor, cliente_id, producto["id"]).json()["pedido_id"]
    assert client.get(f"{API}/pedidos/{pid}", headers=vendedor).json()["pedido_id"] == pid
    lista = client.get(f"{API}/pedidos", params={"cliente_id": cliente_id, "estado": "Pendiente", "size": 5}, headers=vendedor).json()
    assert lista["total"] >= 1 and len(lista["items"]) <= 5
    assert client.get(f"{API}/pedidos/{uuid.uuid4()}", headers=vendedor).status_code == 404
    assert client.get(f"{API}/pedidos/no-es-uuid", headers=vendedor).status_code == 422
    assert client.get(f"{API}/pedidos", params={"size": 1000}, headers=vendedor).status_code == 422


def test_historial_cliente(client, vendedor, cliente_id, producto):
    nuevo_pedido(client, vendedor, cliente_id, producto["id"])
    h = client.get(f"{API}/pedidos/historial/{cliente_id}", headers=vendedor).json()
    assert h["total_pedidos"] >= 1 and Decimal(h["total_comprado"]) > 0


# ---------- Modificar (RF-04) ----------
def test_modificar_pedido(client, vendedor, cliente_id, producto):
    p = nuevo_pedido(client, vendedor, cliente_id, producto["id"], cantidad=1).json()
    r = client.put(f"{API}/pedidos/{p['pedido_id']}", headers=vendedor, json={"items": [{"producto_id": producto["id"], "cantidad": 10}], "descripcion": "Ajustado"})
    assert r.status_code == 200
    m = r.json()
    assert m["detalles"][0]["cantidad"] == 10 and m["descripcion"] == "Ajustado"
    assert Decimal(m["subtotal"]) == producto["precio"] * 10
    assert client.put(f"{API}/pedidos/{p['pedido_id']}", headers=vendedor, json={}).status_code == 422


# ---------- Estados (RF-08) y cancelación (RF-05) ----------
def test_flujo_de_estados_valido(client, vendedor, cliente_id, producto):
    pid = nuevo_pedido(client, vendedor, cliente_id, producto["id"]).json()["pedido_id"]
    for estado in ["Confirmado", "En preparación", "Enviado", "Entregado"]:
        r = client.patch(f"{API}/pedidos/{pid}/estado", json={"estado": estado}, headers=vendedor)
        assert r.status_code == 200 and r.json()["estado"] == estado


def test_transiciones_invalidas(client, vendedor, cliente_id, producto):
    pid = nuevo_pedido(client, vendedor, cliente_id, producto["id"]).json()["pedido_id"]
    assert client.patch(f"{API}/pedidos/{pid}/estado", json={"estado": "Entregado"}, headers=vendedor).status_code == 409
    assert client.patch(f"{API}/pedidos/{pid}/estado", json={"estado": "Inventado"}, headers=vendedor).status_code == 422


def test_cancelar_y_reglas_posteriores(client, vendedor, cliente_id, producto):
    pid = nuevo_pedido(client, vendedor, cliente_id, producto["id"]).json()["pedido_id"]
    assert client.post(f"{API}/pedidos/{pid}/cancelar", json={"motivo": "x"}, headers=vendedor).status_code == 422  # motivo muy corto
    r = client.post(f"{API}/pedidos/{pid}/cancelar", json={"motivo": "Cliente desistió"}, headers=vendedor)
    assert r.status_code == 200 and r.json()["estado"] == "Cancelado"
    assert client.post(f"{API}/pedidos/{pid}/cancelar", json={"motivo": "otra vez"}, headers=vendedor).status_code == 409
    assert client.put(f"{API}/pedidos/{pid}", json={"descripcion": "tarde"}, headers=vendedor).status_code == 409
    assert client.patch(f"{API}/pedidos/{pid}/estado", json={"estado": "Confirmado"}, headers=vendedor).status_code == 409


def test_no_cancela_pedido_enviado(client, vendedor, cliente_id, producto):
    pid = nuevo_pedido(client, vendedor, cliente_id, producto["id"]).json()["pedido_id"]
    for e in ["Confirmado", "En preparación", "Enviado"]:
        client.patch(f"{API}/pedidos/{pid}/estado", json={"estado": e}, headers=vendedor)
    assert client.post(f"{API}/pedidos/{pid}/cancelar", json={"motivo": "ya enviado"}, headers=vendedor).status_code == 409


# ---------- Auditoría (RNF-05) ----------
def test_auditoria_registra_cada_operacion(client, vendedor, cliente_id, producto):
    pid = nuevo_pedido(client, vendedor, cliente_id, producto["id"]).json()["pedido_id"]
    client.put(f"{API}/pedidos/{pid}", json={"descripcion": "cambio"}, headers=vendedor)
    client.patch(f"{API}/pedidos/{pid}/estado", json={"estado": "Confirmado"}, headers=vendedor)
    client.post(f"{API}/pedidos/{pid}/cancelar", json={"motivo": "prueba de auditoría"}, headers=vendedor)
    acciones = [a["accion"] for a in client.get(f"{API}/pedidos/{pid}/auditoria", headers=vendedor).json()]
    assert acciones == ["CREAR", "MODIFICAR", "CAMBIO_ESTADO", "CANCELAR"]


# ---------- Reportes (RF-10) ----------
def test_reporte_ventas_excluye_cancelados(client, vendedor, cliente_id, producto):
    base = client.get(f"{API}/reportes/ventas", headers=vendedor).json()
    ok = nuevo_pedido(client, vendedor, cliente_id, producto["id"], cantidad=2).json()
    malo = nuevo_pedido(client, vendedor, cliente_id, producto["id"], cantidad=7).json()
    client.post(f"{API}/pedidos/{malo['pedido_id']}/cancelar", json={"motivo": "no aplica"}, headers=vendedor)
    nuevo = client.get(f"{API}/reportes/ventas", headers=vendedor).json()
    assert Decimal(nuevo["total_ventas"]) - Decimal(base["total_ventas"]) == Decimal(ok["total"])
    assert nuevo["pedidos_cancelados"] == base["pedidos_cancelados"] + 1
    assert nuevo["total_pedidos"] == base["total_pedidos"] + 2


def test_reporte_csv_y_agrupacion_mensual(client, vendedor):
    r = client.get(f"{API}/reportes/ventas.csv", headers=vendedor)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "periodo,pedidos,subtotal,impuestos,total" in r.text
    m = client.get(f"{API}/reportes/ventas", params={"agrupar": "mes"}, headers=vendedor).json()
    assert all(len(s["periodo"]) == 7 for s in m["serie"])
    assert client.get(f"{API}/reportes/ventas", params={"agrupar": "anio"}, headers=vendedor).status_code == 422


# ---------- Integración (RF-12, CU-05, CU-13) ----------
def test_integracion_requiere_api_key(client, vendedor, cliente_id, producto):
    pid = nuevo_pedido(client, vendedor, cliente_id, producto["id"]).json()["pedido_id"]
    assert client.get(f"{API}/integracion/pedidos/{pid}").status_code == 401
    assert client.get(f"{API}/integracion/pedidos/{pid}", headers={"X-API-Key": "incorrecta"}).status_code == 401
    assert client.get(f"{API}/integracion/pedidos/{pid}", headers=vendedor).status_code == 401  # JWT no sirve aquí
    ok = client.get(f"{API}/integracion/pedidos/{pid}", headers=KEY)
    assert ok.status_code == 200 and ok.json()["pedido_id"] == pid
    assert client.get(f"{API}/integracion/clientes/{cliente_id}/pedidos", headers=KEY).json()["total_pedidos"] >= 1


def test_solicitud_del_cliente_queda_auditada(client, vendedor, cliente_id, producto):
    pid = nuevo_pedido(client, vendedor, cliente_id, producto["id"]).json()["pedido_id"]
    r = client.post(f"{API}/integracion/pedidos/{pid}/solicitudes", headers=KEY, json={"tipo": "cancelacion", "detalle": "Ya no lo necesito", "solicitante": "Cliente"})
    assert r.status_code == 202
    # No modifica el pedido
    assert client.get(f"{API}/pedidos/{pid}", headers=vendedor).json()["estado"] == "Pendiente"
    aud = client.get(f"{API}/pedidos/{pid}/auditoria", headers=vendedor).json()
    assert aud[-1]["accion"] == "SOLICITUD_CANCELACION" and aud[-1]["usuario"] == "Sistema externo"
    sol = client.get(f"{API}/pedidos/solicitudes", headers=vendedor).json()
    assert any(s["pedido_id"] == pid for s in sol)
    assert client.post(f"{API}/integracion/pedidos/{pid}/solicitudes", headers=KEY, json={"tipo": "otra", "detalle": "xx"}).status_code == 422


# ---------- Seguridad (RNF-04) ----------
def test_sql_injection_en_filtros_no_rompe(client, vendedor):
    r = client.get(f"{API}/pedidos", params={"estado": "' OR 1=1; DROP TABLE pedido;--"}, headers=vendedor)
    assert r.status_code == 200 and r.json()["total"] == 0
    assert client.get(f"{API}/catalogo/productos", params={"q": "'; DROP TABLE x;--"}, headers=vendedor).status_code == 200


def test_cabeceras_de_seguridad(client):
    h = client.get("/health").headers
    assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
    assert "default-src 'self'" in client.get("/").headers["content-security-policy"]

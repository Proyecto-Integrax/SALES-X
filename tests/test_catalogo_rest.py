"""Proveedor REST del catálogo (CATALOGO_PROVIDER=rest) contra servicios HTTP reales de Clientes y Productos.

Se levanta el servicio simulado (`mocks/integrax_mock.py`) en un puerto libre y se prueba:
  * el adaptador `CatalogoRest` directamente (éxito, 404, caída, timeout, errores, respuestas inválidas), y
  * la API de SALES-X completa usando ese adaptador (precios y existencias salen del servicio externo).
"""

import socket
import threading
import time
import uuid
from decimal import Decimal

import httpx
import pytest
import uvicorn
from fastapi import HTTPException

import app.integration.catalogo as cat_mod
from app.config import Settings
from app.integration.catalogo import CatalogoRest, get_catalogo
from app.main import app as sales_app
from mocks import integrax_mock

API = "/api/v1"


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def mock_url():
    port = _puerto_libre()
    server = uvicorn.Server(uvicorn.Config(integrax_mock.app, host="127.0.0.1", port=port, log_level="error"))
    hilo = threading.Thread(target=server.run, daemon=True)
    hilo.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    assert server.started, "el servicio simulado no arrancó"
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    hilo.join(timeout=5)


@pytest.fixture(autouse=True)
def _restablecer(mock_url):
    httpx.post(f"{mock_url}/_admin/reset")
    yield
    httpx.post(f"{mock_url}/_admin/reset")


def fabricar(monkeypatch, base: str, timeout: float = 2.0) -> CatalogoRest:
    s = Settings(clientes_api_url=f"{base}/api/clientes", productos_api_url=f"{base}/api/productos", integration_timeout_seconds=timeout)
    monkeypatch.setattr(cat_mod, "get_settings", lambda: s)
    return CatalogoRest()


@pytest.fixture()
def rest(monkeypatch, mock_url):
    return fabricar(monkeypatch, mock_url)


def producto_mock(mock_url, sku):
    return next(p for p in httpx.get(f"{mock_url}/api/productos").json() if p["sku"] == sku)


# ======================= El adaptador, directamente =======================
def test_lista_y_obtiene_clientes_y_productos(rest, mock_url):
    clientes = rest.listar_clientes()
    assert len(clientes) == 3 and isinstance(clientes[0]["cliente_id"], uuid.UUID)
    assert [c["nombre"] for c in rest.listar_clientes("cafeter")] == ["Cafetería La Esquina"]
    uno = rest.obtener_cliente(clientes[0]["cliente_id"])
    assert uno["nombre"] == clientes[0]["nombre"]

    productos = rest.listar_productos()
    assert len(productos) == 5 and all(isinstance(p["precio"], Decimal) for p in productos)
    assert [p["sku"] for p in rest.listar_productos("HER-002")] == ["HER-002"]
    destornilladores = next(p for p in productos if p["sku"] == "HER-002")
    assert destornilladores["precio"] == Decimal("45500.5")  # un precio JSON con decimales no pierde exactitud
    assert rest.obtener_producto(destornilladores["producto_id"])["disponible"] == 200


def test_inexistente_devuelve_none(rest):
    assert rest.obtener_cliente(uuid.uuid4()) is None
    assert rest.obtener_producto(uuid.uuid4()) is None


def test_servicio_caido_da_502(monkeypatch):
    muerto = fabricar(monkeypatch, f"http://127.0.0.1:{_puerto_libre()}")  # nadie escucha ahí
    with pytest.raises(HTTPException) as e:
        muerto.listar_productos()
    assert e.value.status_code == 502


def test_error_500_del_servicio_da_502(rest, mock_url):
    httpx.post(f"{mock_url}/_admin/modo", json={"falla": "500"})
    with pytest.raises(HTTPException) as e:
        rest.listar_clientes()
    assert e.value.status_code == 502


def test_timeout_da_502_y_no_se_cuelga(monkeypatch, mock_url):
    lento = fabricar(monkeypatch, mock_url, timeout=0.3)
    httpx.post(f"{mock_url}/_admin/modo", json={"lento": 1.5})
    inicio = time.monotonic()
    with pytest.raises(HTTPException) as e:
        lento.listar_productos()
    assert e.value.status_code == 502 and time.monotonic() - inicio < 1.2  # respeta el tiempo máximo


@pytest.mark.parametrize("falla", ["malformado", "no_json"])
def test_respuesta_invalida_da_502_y_no_error_interno(rest, mock_url, falla):
    httpx.post(f"{mock_url}/_admin/modo", json={"falla": falla})
    for llamada in (rest.listar_clientes, rest.listar_productos):
        with pytest.raises(HTTPException) as e:
            llamada()
        assert e.value.status_code == 502, f"{falla}/{llamada.__name__} produjo {e.value.status_code}"
    uid = uuid.uuid4()
    for llamada in (rest.obtener_cliente, rest.obtener_producto):
        with pytest.raises(HTTPException) as e:
            llamada(uid)
        assert e.value.status_code == 502


# ======================= La API de SALES-X usando el servicio externo =======================
@pytest.fixture()
def api_rest(rest, client):
    sales_app.dependency_overrides[get_catalogo] = lambda: rest
    yield client
    sales_app.dependency_overrides.pop(get_catalogo, None)


def total_pedidos(c, h):
    return c.get(f"{API}/pedidos", params={"size": 1}, headers=h).json()["total"]


def test_pedido_con_precios_y_existencias_del_servicio_externo(api_rest, vendedor, mock_url):
    cliente = httpx.get(f"{mock_url}/api/clientes").json()[0]["cliente_id"]
    taladro = producto_mock(mock_url, "HER-001")
    r = api_rest.post(f"{API}/pedidos", headers=vendedor, json={"cliente_id": cliente, "items": [{"producto_id": taladro["producto_id"], "cantidad": 2}]})
    assert r.status_code == 201, r.text
    p = r.json()
    assert Decimal(p["detalles"][0]["precio_unitario"]) == Decimal("289900")  # precio del servicio, no del catálogo simulado
    assert Decimal(p["subtotal"]) == Decimal("579800.00") and Decimal(p["impuestos"]) == Decimal("110162.00")
    assert Decimal(p["total"]) == Decimal("689962.00")


def test_precio_con_decimales_se_calcula_exacto(api_rest, vendedor, mock_url):
    cliente = httpx.get(f"{mock_url}/api/clientes").json()[1]["cliente_id"]
    dest = producto_mock(mock_url, "HER-002")
    p = api_rest.post(f"{API}/pedidos", headers=vendedor, json={"cliente_id": cliente, "items": [{"producto_id": dest["producto_id"], "cantidad": 3}]}).json()
    assert Decimal(p["subtotal"]) == Decimal("136501.50") and Decimal(p["total"]) == Decimal("162436.79")


def test_reglas_de_negocio_con_datos_externos(api_rest, vendedor, mock_url):
    cliente = httpx.get(f"{mock_url}/api/clientes").json()[0]["cliente_id"]

    def pedir(producto_id, cantidad, cli=cliente):
        return api_rest.post(f"{API}/pedidos", headers=vendedor, json={"cliente_id": cli, "items": [{"producto_id": producto_id, "cantidad": cantidad}]})

    tornillos = producto_mock(mock_url, "HER-003")  # 3 en existencia
    assert pedir(tornillos["producto_id"], 4).status_code == 409
    assert pedir(tornillos["producto_id"], 3).status_code == 201
    assert pedir(producto_mock(mock_url, "HER-004")["producto_id"], 1).status_code == 409  # agotado
    assert pedir(producto_mock(mock_url, "HER-005")["producto_id"], 1).status_code == 422  # inactivo
    assert pedir(tornillos["producto_id"], 1, cli=str(uuid.uuid4())).status_code == 422  # cliente inexistente en el servicio
    assert pedir(str(uuid.uuid4()), 1).status_code == 422  # producto inexistente en el servicio


def test_las_existencias_se_leen_en_vivo_sin_cache(api_rest, vendedor, mock_url):
    tornillos = producto_mock(mock_url, "HER-003")
    url = f"{API}/catalogo/productos/{tornillos['producto_id']}/disponibilidad"
    assert api_rest.get(url, headers=vendedor).json()["disponible"] == 3
    httpx.post(f"{mock_url}/_admin/productos/{tornillos['producto_id']}", json={"disponible": 50})
    assert api_rest.get(url, headers=vendedor).json()["disponible"] == 50
    cliente = httpx.get(f"{mock_url}/api/clientes").json()[0]["cliente_id"]
    r = api_rest.post(f"{API}/pedidos", headers=vendedor, json={"cliente_id": cliente, "items": [{"producto_id": tornillos["producto_id"], "cantidad": 40}]})
    assert r.status_code == 201


def test_catalogo_y_integracion_reflejan_el_servicio_externo(api_rest, vendedor, mock_url):
    nombres = [c["nombre"] for c in api_rest.get(f"{API}/catalogo/clientes", headers=vendedor).json()]
    assert "Colegio San Martín" in nombres
    taladro = producto_mock(mock_url, "HER-001")
    r = api_rest.get(f"{API}/integracion/disponibilidad/{taladro['producto_id']}", headers={"X-API-Key": "api-key-de-pruebas"})
    assert r.status_code == 200 and r.json()["disponible"] == 40


def test_servicio_externo_caido_no_crea_pedidos_y_responde_502(api_rest, vendedor, mock_url):
    cliente = httpx.get(f"{mock_url}/api/clientes").json()[0]["cliente_id"]
    taladro = producto_mock(mock_url, "HER-001")
    antes = total_pedidos(api_rest, vendedor)
    httpx.post(f"{mock_url}/_admin/modo", json={"falla": "500"})
    r = api_rest.post(f"{API}/pedidos", headers=vendedor, json={"cliente_id": cliente, "items": [{"producto_id": taladro["producto_id"], "cantidad": 1}]})
    assert r.status_code == 502
    assert api_rest.get(f"{API}/catalogo/productos", headers=vendedor).status_code == 502
    assert total_pedidos(api_rest, vendedor) == antes  # nada quedó a medias


def test_respuesta_invalida_del_servicio_da_502_en_la_api(api_rest, vendedor, mock_url):
    httpx.post(f"{mock_url}/_admin/modo", json={"falla": "malformado"})
    assert api_rest.get(f"{API}/catalogo/productos", headers=vendedor).status_code == 502
    assert api_rest.get(f"{API}/catalogo/clientes", headers=vendedor).status_code == 502

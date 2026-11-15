import os
import tempfile
from pathlib import Path

# Configuración de pruebas: DEBE definirse antes de importar la app.
_tmp = Path(tempfile.mkdtemp()) / "test.db"
# Por defecto SQLite temporal; con TEST_DATABASE_URL se prueba sobre PostgreSQL (la base debe terminar en "_test").
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{_tmp.as_posix()}"
os.environ["SECRET_KEY"] = "clave-de-pruebas-0123456789-0123456789"
os.environ["INTEGRATION_API_KEY"] = "api-key-de-pruebas"
os.environ["ADMIN_EMAIL"] = "admin@test.local"
os.environ["ADMIN_PASSWORD"] = "AdminTest2026*"
os.environ["SEED_DEMO_USERS"] = "true"
os.environ["CATALOGO_PROVIDER"] = "simulado"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.integration.catalogo import get_catalogo  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.database import Base, engine

    url = engine.url
    # Protección: solo se limpia SQLite temporal o una base cuyo nombre termine en "_test".
    assert url.get_backend_name() == "sqlite" or (url.database or "").endswith("_test"), "Las pruebas solo pueden limpiar bases *_test"
    if not os.environ.get("TEST_KEEP_SCHEMA"):  # TEST_KEEP_SCHEMA=1: usar el esquema ya creado con sql/01_schema.sql
        Base.metadata.drop_all(engine)
    with TestClient(app) as c:
        yield c


def _login(client, correo, contrasena):
    r = client.post("/api/v1/auth/login", json={"correo": correo, "contrasena": contrasena})
    assert r.status_code == 200, r.text
    client.cookies.clear()  # las pruebas autentican con cabecera Bearer; la cookie de sesión se prueba aparte
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client):
    return _login(client, "admin@test.local", "AdminTest2026*")


@pytest.fixture(scope="session")
def vendedor(client):
    return _login(client, "vendedor@salesx.local", "Ventas2026*")


@pytest.fixture(scope="session")
def catalogo():
    return get_catalogo()


@pytest.fixture()
def cliente_id(catalogo):
    return str(catalogo.listar_clientes()[0]["cliente_id"])


@pytest.fixture()
def producto(catalogo):
    """Producto con buen stock y su precio."""
    p = next(p for p in catalogo.listar_productos() if p["sku"] == "TEC-002")  # Mouse, 55.000
    return {"id": str(p["producto_id"]), "precio": p["precio"], "disponible": p["disponible"]}


@pytest.fixture()
def agotado(catalogo):
    return str(next(p for p in catalogo.listar_productos() if p["disponible"] == 0)["producto_id"])

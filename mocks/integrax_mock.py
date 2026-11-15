"""Servicios SIMULADOS de Clientes y Productos de INTEGRAX (solo para pruebas).

Implementan el contrato REST que SALES-X espera de los otros microproyectos (ver
`app/integration/catalogo.py` y docs/Guia-de-Operacion-y-Despliegue.md §5.1):

    GET /api/clientes            GET /api/clientes/{id}
    GET /api/productos           GET /api/productos/{id}

Además exponen utilidades de prueba bajo /_admin para forzar situaciones difíciles:
latencia, errores 500, respuestas malformadas o cambios de existencias.

Ejecutar:  python -m uvicorn mocks.integrax_mock:app --port 8001
NO usar en producción: no tiene autenticación.
"""

import asyncio
import copy
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

_NS = uuid.UUID("a1b2c3d4-0000-4000-8000-00000000cafe")


def _id(nombre: str) -> str:
    return str(uuid.uuid5(_NS, nombre))


_CLIENTES = [
    {"cliente_id": _id(n), "nombre": n, "documento": d, "correo": c}
    for n, d, c in [
        ("Ferretería El Tornillo S.A.S.", "900111222-3", "compras@tornillo.example"),
        ("Cafetería La Esquina", "1015432100", "pedidos@laesquina.example"),
        ("Colegio San Martín", "890333444-5", "tesoreria@sanmartin.example"),
    ]
]
_PRODUCTOS = [
    {"producto_id": _id(n), "nombre": n, "sku": sku, "precio": precio, "disponible": stock, "activo": activo}
    for n, sku, precio, stock, activo in [
        ("Taladro percutor 650W", "HER-001", 289900, 40, True),
        ("Juego de destornilladores x12", "HER-002", 45500.50, 200, True),
        ("Caja de tornillos x500", "HER-003", 18900, 3, True),
        ("Sierra circular (agotada)", "HER-004", 359000, 0, True),
        ("Lijadora (descontinuada)", "HER-005", 199000, 25, False),
    ]
]

ESTADO: dict = {}
DATOS: dict = {}


def reset() -> None:
    DATOS["clientes"] = copy.deepcopy(_CLIENTES)
    DATOS["productos"] = copy.deepcopy(_PRODUCTOS)
    ESTADO.clear()
    ESTADO.update({"lento": 0.0, "falla": None})


reset()
app = FastAPI(title="INTEGRAX · servicios simulados (Clientes y Productos)", docs_url="/docs")


@app.middleware("http")
async def inyectar_fallas(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        if ESTADO["lento"]:
            await asyncio.sleep(ESTADO["lento"])
        if ESTADO["falla"] == "500":
            return JSONResponse({"detail": "fallo interno simulado"}, status_code=500)
        if ESTADO["falla"] == "no_json":
            return Response("<html><body>Bad gateway</body></html>", status_code=200, media_type="text/html")
        if ESTADO["falla"] == "malformado":
            es_lista = request.url.path.rstrip("/").count("/") == 2
            return JSONResponse([{"foo": "bar"}] if es_lista else {"foo": "bar"})
    return await call_next(request)


def _buscar(coleccion: str, clave: str, valor: str):
    return next((x for x in DATOS[coleccion] if x[clave] == valor), None)


@app.get("/api/clientes")
def clientes():
    return DATOS["clientes"]


@app.get("/api/clientes/{cliente_id}")
def cliente(cliente_id: str):
    c = _buscar("clientes", "cliente_id", cliente_id)
    if not c:
        raise HTTPException(404, "Cliente no encontrado")
    return c


@app.get("/api/productos")
def productos():
    return DATOS["productos"]


@app.get("/api/productos/{producto_id}")
def producto(producto_id: str):
    p = _buscar("productos", "producto_id", producto_id)
    if not p:
        raise HTTPException(404, "Producto no encontrado")
    return p


# ---------- utilidades de prueba ----------
class Modo(BaseModel):
    lento: float = 0.0  # segundos de espera antes de responder
    falla: str | None = None  # None | "500" | "malformado" | "no_json"


class Existencias(BaseModel):
    disponible: int | None = None
    activo: bool | None = None


@app.post("/_admin/modo")
def modo(m: Modo):
    ESTADO.update(m.model_dump())
    return ESTADO


@app.post("/_admin/productos/{producto_id}")
def cambiar(producto_id: str, e: Existencias):
    p = _buscar("productos", "producto_id", producto_id)
    if not p:
        raise HTTPException(404, "Producto no encontrado")
    if e.disponible is not None:
        p["disponible"] = e.disponible
    if e.activo is not None:
        p["activo"] = e.activo
    return p


@app.post("/_admin/reset")
def restablecer():
    reset()
    return {"ok": True}

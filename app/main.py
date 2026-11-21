import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from . import __version__, models  # noqa: F401  (registra los modelos)
from .config import get_settings, validate_for_production
from .database import Base, SessionLocal, engine
from .routers import auth, catalogo, consumidores, integracion, pedidos, reportes
from .integration.catalogo import get_catalogo
from .seed import seed
from .services.pedidos import sincronizar_catalogo

STATIC_DIR = Path(__file__).parent / "static"
settings = get_settings()


log = logging.getLogger("salesx")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment == "production":
        problems = validate_for_production(settings)
        if problems:
            raise RuntimeError("Configuración insegura para producción: " + "; ".join(problems))
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
        try:  # copia local de clientes y productos (FK); si el catálogo externo no responde, se sincroniza al crear pedidos
            sincronizar_catalogo(db, get_catalogo())
        except Exception:
            log.warning("No se pudo sincronizar el catálogo al iniciar", exc_info=True)
            db.rollback()
    yield


app = FastAPI(
    title="SALES-X - Gestión de Ventas y Pedidos",
    version=__version__,
    description="Microproyecto SALES-X de INTEGRAX: registro, gestión y reporte de pedidos de venta.",
    lifespan=lifespan,
)

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-CSRF-Token"],
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    if settings.environment == "production":
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if not request.url.path.startswith(("/docs", "/redoc", "/openapi")):
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'",
        )
    return resp


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):  # no filtrar trazas al cliente, pero sí registrarlas
    log.error("Error no controlado en %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse({"detail": "Error interno del servidor"}, status_code=500)


API = "/api/v1"
for r in (auth.router, consumidores.router, catalogo.router, pedidos.router, reportes.router, integracion.router):
    app.include_router(r, prefix=API)


@app.get("/health", tags=["Operación"], summary="Estado del servicio")
def health():
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        db = "ok"
    except Exception:
        db = "error"
    return JSONResponse({"status": "ok" if db == "ok" else "degraded", "database": db, "version": __version__,
                         "iva_rate": settings.iva_rate},
                        status_code=200 if db == "ok" else 503)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/static/index.html")

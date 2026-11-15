"""Puerto de integración con los demás microproyectos de INTEGRAX.

SALES-X no es dueño de Clientes ni de Productos/Inventario: sólo guarda sus
identificadores. Esta capa abstrae de dónde salen esos datos:

* ``simulado`` : catálogo de demostración interno (por defecto, para desarrollo y pruebas).
* ``rest``     : consume los servicios REST de los microproyectos de Clientes y Productos.

Contrato REST esperado (JSON):
    GET {CLIENTES_API_URL}                 -> [{"cliente_id","nombre","documento","correo"}]
    GET {CLIENTES_API_URL}/{id}            -> {"cliente_id","nombre","documento","correo"}   (404 si no existe)
    GET {PRODUCTOS_API_URL}                -> [{"producto_id","nombre","sku","precio","disponible","activo"}]
    GET {PRODUCTOS_API_URL}/{id}           -> {...mismo formato...}                          (404 si no existe)
"""

import uuid
from decimal import Decimal
from typing import Protocol

import httpx
from fastapi import HTTPException

from ..config import get_settings

_NS = uuid.UUID("6f1c2d3e-5a4b-4c7d-8e9f-0a1b2c3d4e5f")


def _id(name: str) -> uuid.UUID:
    return uuid.uuid5(_NS, name)


class CatalogoClient(Protocol):
    def listar_clientes(self, q: str | None = None) -> list[dict]: ...
    def obtener_cliente(self, cliente_id: uuid.UUID) -> dict | None: ...
    def listar_productos(self, q: str | None = None) -> list[dict]: ...
    def obtener_producto(self, producto_id: uuid.UUID) -> dict | None: ...


def _match(item: dict, q: str | None, fields: tuple[str, ...]) -> bool:
    if not q:
        return True
    q = q.lower()
    return any(q in str(item.get(f, "")).lower() for f in fields)


class CatalogoSimulado:
    """Datos de demostración estables (los UUID se derivan del nombre)."""

    def __init__(self) -> None:
        clientes = [
            ("Comercial La Estrella S.A.S.", "900123456-1", "compras@laestrella.example"),
            ("Distribuidora Andina Ltda.", "800987654-3", "pedidos@andina.example"),
            ("Papelería El Punto", "1020304050", "contacto@elpunto.example"),
            ("Supermercado Central", "901555222-7", "admin@supercentral.example"),
            ("María Fernanda Gómez", "43123456", "mafe.gomez@example.com"),
        ]
        productos = [
            ("Laptop 14\" Core i5", "TEC-001", "2850000", 25),
            ("Mouse inalámbrico", "TEC-002", "55000", 300),
            ("Teclado mecánico", "TEC-003", "189000", 80),
            ("Monitor 24\" Full HD", "TEC-004", "720000", 40),
            ("Impresora multifuncional", "OFI-001", "540000", 15),
            ("Resma papel carta x500", "OFI-002", "18500", 1200),
            ("Silla ergonómica", "MOB-001", "430000", 20),
            ("Escritorio 120x60", "MOB-002", "390000", 12),
            ("Cable HDMI 2m", "ACC-001", "22000", 500),
            ("Disco SSD 1TB", "TEC-005", "310000", 0),  # agotado a propósito (demostración)
        ]
        self._clientes = {
            _id(n): {"cliente_id": _id(n), "nombre": n, "documento": d, "correo": c} for n, d, c in clientes
        }
        self._productos = {
            _id(n): {
                "producto_id": _id(n),
                "nombre": n,
                "sku": sku,
                "precio": Decimal(precio),
                "disponible": stock,
                "activo": True,
            }
            for n, sku, precio, stock in productos
        }

    def listar_clientes(self, q=None):
        return [c for c in self._clientes.values() if _match(c, q, ("nombre", "documento", "correo"))]

    def obtener_cliente(self, cliente_id):
        return self._clientes.get(cliente_id)

    def listar_productos(self, q=None):
        return [p for p in self._productos.values() if _match(p, q, ("nombre", "sku"))]

    def obtener_producto(self, producto_id):
        return self._productos.get(producto_id)


class CatalogoRest:
    def __init__(self) -> None:
        s = get_settings()
        self._clientes_url = s.clientes_api_url.rstrip("/")
        self._productos_url = s.productos_api_url.rstrip("/")
        self._timeout = s.integration_timeout_seconds
        # Un único cliente HTTP reutilizado: mantiene conexiones abiertas (keep-alive) y evita crear el contexto
        # TLS en cada consulta (medido: ~185 ms por consulta con un cliente nuevo cada vez). Es seguro entre hilos.
        self._http = httpx.Client(timeout=self._timeout)

    def _get(self, url: str) -> dict | list | None:
        try:
            r = self._http.get(url)
        except httpx.HTTPError as exc:
            raise HTTPException(502, "Servicio externo de INTEGRAX no disponible") from exc
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            raise HTTPException(502, f"Servicio externo respondió {r.status_code}")
        try:
            return r.json()
        except ValueError as exc:  # no es JSON (p. ej. una página de error HTML de un proxy)
            raise HTTPException(502, "Respuesta inválida del servicio externo") from exc

    @staticmethod
    def _leer(convertir, dato):
        """Convierte un registro externo; si no cumple el contrato es un fallo del servicio (502), no un error interno."""
        try:
            return convertir(dato)
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            raise HTTPException(502, "Respuesta inválida del servicio externo") from exc

    def _lista(self, url: str, convertir) -> list[dict]:
        data = self._get(url)
        if data is None:
            return []
        if not isinstance(data, list):
            raise HTTPException(502, "Respuesta inválida del servicio externo")
        return [self._leer(convertir, d) for d in data]

    @staticmethod
    def _cliente(d: dict) -> dict:
        return {
            "cliente_id": uuid.UUID(str(d["cliente_id"])),
            "nombre": d["nombre"],
            "documento": d.get("documento"),
            "correo": d.get("correo"),
        }

    @staticmethod
    def _producto(d: dict) -> dict:
        return {
            "producto_id": uuid.UUID(str(d["producto_id"])),
            "nombre": d["nombre"],
            "sku": d.get("sku"),
            "precio": Decimal(str(d["precio"])),
            "disponible": int(d.get("disponible", 0)),
            "activo": bool(d.get("activo", True)),
        }

    def listar_clientes(self, q=None):
        return [c for c in self._lista(self._clientes_url, self._cliente) if _match(c, q, ("nombre", "documento", "correo"))]

    def obtener_cliente(self, cliente_id):
        d = self._get(f"{self._clientes_url}/{cliente_id}")
        return self._leer(self._cliente, d) if d else None

    def listar_productos(self, q=None):
        return [p for p in self._lista(self._productos_url, self._producto) if _match(p, q, ("nombre", "sku"))]

    def obtener_producto(self, producto_id):
        d = self._get(f"{self._productos_url}/{producto_id}")
        return self._leer(self._producto, d) if d else None


_instance: CatalogoClient | None = None


def get_catalogo() -> CatalogoClient:
    global _instance
    if _instance is None:
        _instance = CatalogoRest() if get_settings().catalogo_provider == "rest" else CatalogoSimulado()
    return _instance

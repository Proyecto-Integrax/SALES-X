import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import current_user
from ..integration.catalogo import CatalogoClient, get_catalogo
from ..schemas import ClienteOut, DisponibilidadOut, ProductoOut

router = APIRouter(prefix="/catalogo", tags=["Catálogo (INTEGRAX)"], dependencies=[Depends(current_user)])


@router.get("/clientes", response_model=list[ClienteOut], summary="Consultar clientes")
def clientes(q: str | None = Query(default=None, max_length=80), cat: CatalogoClient = Depends(get_catalogo)):
    return cat.listar_clientes(q)


@router.get("/productos", response_model=list[ProductoOut], summary="Consultar productos y disponibilidad")
def productos(q: str | None = Query(default=None, max_length=80), cat: CatalogoClient = Depends(get_catalogo)):
    return cat.listar_productos(q)


@router.get(
    "/productos/{producto_id}/disponibilidad", response_model=DisponibilidadOut, summary="Disponibilidad de un producto (RF-11)"
)
def disponibilidad(producto_id: uuid.UUID, cat: CatalogoClient = Depends(get_catalogo)):
    p = cat.obtener_producto(producto_id)
    if not p:
        raise HTTPException(404, "Producto no encontrado")
    return DisponibilidadOut(producto_id=p["producto_id"], nombre=p["nombre"], disponible=p["disponible"], activo=p["activo"])

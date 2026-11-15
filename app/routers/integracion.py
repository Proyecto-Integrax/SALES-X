"""Servicios de integración para otros sistemas de INTEGRAX (RF-12).

Se autentican con la cabecera ``X-API-Key`` (no con sesión de usuario).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_api_key
from ..integration.catalogo import CatalogoClient, get_catalogo
from ..models import ConsumidorApi, Pedido
from ..schemas import DisponibilidadOut, HistorialCliente, PedidoOut, PedidoResumen, SolicitudIn, SolicitudOut
from ..services import pedidos as svc

router = APIRouter(prefix="/integracion", tags=["Integración INTEGRAX"], dependencies=[Depends(require_api_key)])


@router.get("/pedidos/{pedido_id}", response_model=PedidoOut, summary="Consultar un pedido")
def pedido(pedido_id: uuid.UUID, db: Session = Depends(get_db)):
    return svc.obtener_pedido(db, pedido_id)


@router.get("/clientes/{cliente_id}/pedidos", response_model=HistorialCliente, summary="Pedidos de un cliente")
def pedidos_cliente(cliente_id: uuid.UUID, db: Session = Depends(get_db)):
    rows = db.scalars(select(Pedido).where(Pedido.cliente_id == cliente_id).order_by(Pedido.fecha_creacion.desc())).all()
    comprado = sum((p.total for p in rows if p.estado.nombre != "Cancelado"), start=0)
    return HistorialCliente(
        cliente_id=cliente_id, total_pedidos=len(rows), total_comprado=comprado, pedidos=[PedidoResumen.model_validate(p) for p in rows]
    )


@router.get("/disponibilidad/{producto_id}", response_model=DisponibilidadOut, summary="Disponibilidad de un producto")
def disponibilidad(producto_id: uuid.UUID, cat: CatalogoClient = Depends(get_catalogo)):
    p = cat.obtener_producto(producto_id)
    if not p:
        raise HTTPException(404, "Producto no encontrado")
    return DisponibilidadOut(producto_id=p["producto_id"], nombre=p["nombre"], disponible=p["disponible"], activo=p["activo"])


@router.post(
    "/pedidos/{pedido_id}/solicitudes",
    response_model=SolicitudOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitud de modificación o cancelación del cliente (CU-05)",
)
def solicitar(
    pedido_id: uuid.UUID, data: SolicitudIn, db: Session = Depends(get_db), consumidor: ConsumidorApi = Depends(require_api_key)
):
    """No modifica el pedido: deja constancia auditada para que el área de ventas la gestione."""
    p = svc.obtener_pedido(db, pedido_id)
    quien = f" (solicitante: {data.solicitante})" if data.solicitante else ""
    svc.registrar_auditoria(
        db, p.pedido_id, None, f"SOLICITUD_{data.tipo.upper()}", f"{data.detalle}{quien} · consumidor: {consumidor.nombre}"
    )
    db.commit()
    return SolicitudOut(
        pedido_id=p.pedido_id, tipo=data.tipo, mensaje="Solicitud recibida; el área de ventas la revisará."
    )

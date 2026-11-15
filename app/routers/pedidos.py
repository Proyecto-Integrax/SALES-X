import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import current_user
from ..integration.catalogo import CatalogoClient, get_catalogo
from ..models import AuditoriaPedido, EstadoPedido, Pedido, Vendedor
from ..schemas import (
    AuditoriaOut,
    CancelarIn,
    EstadoChange,
    EstadoOut,
    HistorialCliente,
    Page,
    PedidoCreate,
    PedidoOut,
    PedidoResumen,
    PedidoUpdate,
)
from ..services import pedidos as svc
from ..timeutil import day_end, day_start

router = APIRouter(tags=["Pedidos"], dependencies=[Depends(current_user)])


def _filtros(estado, cliente_id, vendedor_id, desde, hasta):
    conds = []
    if estado:
        conds.append(Pedido.estado.has(EstadoPedido.nombre == estado))
    if cliente_id:
        conds.append(Pedido.cliente_id == cliente_id)
    if vendedor_id:
        conds.append(Pedido.vendedor_id == vendedor_id)
    if desde:
        conds.append(Pedido.fecha_creacion >= day_start(desde))
    if hasta:
        conds.append(Pedido.fecha_creacion <= day_end(hasta))
    return conds


@router.get("/estados", response_model=list[EstadoOut], summary="Estados de pedido")
def estados(db: Session = Depends(get_db)):
    return db.scalars(select(EstadoPedido)).all()


@router.post("/pedidos", response_model=PedidoOut, status_code=201, summary="Registrar pedido (RF-01/02/03/07)")
def crear(
    data: PedidoCreate,
    db: Session = Depends(get_db),
    user: Vendedor = Depends(current_user),
    cat: CatalogoClient = Depends(get_catalogo),
):
    return svc.crear_pedido(db, cat, user, data.cliente_id, data.descripcion, data.items)


@router.get("/pedidos", response_model=Page, summary="Consultar pedidos (RF-06)")
def listar(
    estado: str | None = Query(default=None, max_length=40),
    cliente_id: uuid.UUID | None = None,
    vendedor_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    conds = _filtros(estado, cliente_id, vendedor_id, desde, hasta)
    total = db.scalar(select(func.count()).select_from(Pedido).where(*conds)) or 0
    rows = db.scalars(
        select(Pedido).where(*conds).order_by(Pedido.fecha_creacion.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return Page(items=[PedidoResumen.model_validate(r) for r in rows], total=total, page=page, size=size)


# Rutas fijas ANTES de /pedidos/{pedido_id}
@router.get("/pedidos/solicitudes", response_model=list[AuditoriaOut], summary="Solicitudes de clientes recibidas (CU-05)")
def solicitudes(limit: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db)):
    return db.scalars(
        select(AuditoriaPedido).where(AuditoriaPedido.accion.like("SOLICITUD_%")).order_by(AuditoriaPedido.fecha.desc()).limit(limit)
    ).all()


@router.get("/pedidos/historial/{cliente_id}", response_model=HistorialCliente, summary="Historial de pedidos de un cliente (RF-09)")
def historial(cliente_id: uuid.UUID, db: Session = Depends(get_db)):
    rows = db.scalars(select(Pedido).where(Pedido.cliente_id == cliente_id).order_by(Pedido.fecha_creacion.desc())).all()
    comprado = sum((p.total for p in rows if p.estado.nombre != "Cancelado"), Decimal("0"))
    return HistorialCliente(
        cliente_id=cliente_id,
        total_pedidos=len(rows),
        total_comprado=comprado,
        pedidos=[PedidoResumen.model_validate(p) for p in rows],
    )


@router.get("/pedidos/{pedido_id}", response_model=PedidoOut, summary="Detalle de un pedido")
def detalle(pedido_id: uuid.UUID, db: Session = Depends(get_db)):
    return svc.obtener_pedido(db, pedido_id)


@router.put("/pedidos/{pedido_id}", response_model=PedidoOut, summary="Modificar pedido (RF-04)")
def modificar(
    pedido_id: uuid.UUID,
    data: PedidoUpdate,
    db: Session = Depends(get_db),
    user: Vendedor = Depends(current_user),
    cat: CatalogoClient = Depends(get_catalogo),
):
    return svc.modificar_pedido(db, cat, user, svc.obtener_pedido(db, pedido_id, bloquear=True), data.descripcion, data.items)


@router.patch("/pedidos/{pedido_id}/estado", response_model=PedidoOut, summary="Gestionar estado del pedido (RF-08)")
def estado(pedido_id: uuid.UUID, data: EstadoChange, db: Session = Depends(get_db), user: Vendedor = Depends(current_user)):
    return svc.cambiar_estado(db, user, svc.obtener_pedido(db, pedido_id, bloquear=True), data.estado, data.comentario)


@router.post("/pedidos/{pedido_id}/cancelar", response_model=PedidoOut, summary="Cancelar pedido (RF-05)")
def cancelar(pedido_id: uuid.UUID, data: CancelarIn, db: Session = Depends(get_db), user: Vendedor = Depends(current_user)):
    return svc.cancelar_pedido(db, user, svc.obtener_pedido(db, pedido_id, bloquear=True), data.motivo)


@router.get("/pedidos/{pedido_id}/auditoria", response_model=list[AuditoriaOut], summary="Auditoría del pedido (RNF-05)")
def auditoria(pedido_id: uuid.UUID, db: Session = Depends(get_db)):
    svc.obtener_pedido(db, pedido_id)
    return db.scalars(
        select(AuditoriaPedido).where(AuditoriaPedido.pedido_id == pedido_id).order_by(AuditoriaPedido.fecha.asc())
    ).all()

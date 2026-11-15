"""Reglas de negocio de pedidos (RF-01 .. RF-10)."""

import uuid
from collections import OrderedDict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, lazyload

from ..config import get_settings
from ..integration.catalogo import CatalogoClient
from ..models import AuditoriaPedido, DetallePedido, EstadoPedido, Pedido, Vendedor
from ..schemas import ItemIn

ESTADOS = [
    ("Pendiente", "Pedido registrado, pendiente de confirmación"),
    ("Confirmado", "Pedido confirmado con el cliente"),
    ("En preparación", "Pedido en alistamiento"),
    ("Enviado", "Pedido despachado al cliente"),
    ("Entregado", "Pedido recibido por el cliente"),
    ("Cancelado", "Pedido cancelado"),
]

# Máquina de estados del pedido
TRANSICIONES: dict[str, set[str]] = {
    "Pendiente": {"Confirmado", "Cancelado"},
    "Confirmado": {"En preparación", "Cancelado"},
    "En preparación": {"Enviado", "Cancelado"},
    "Enviado": {"Entregado"},
    "Entregado": set(),
    "Cancelado": set(),
}
MODIFICABLES = {"Pendiente", "Confirmado"}


def registrar_auditoria(
    db: Session, pedido_id: uuid.UUID, vendedor_id: uuid.UUID | None, accion: str, descripcion: str | None
) -> None:
    db.add(AuditoriaPedido(pedido_id=pedido_id, vendedor_id=vendedor_id, accion=accion, descripcion=descripcion))


def obtener_estado(db: Session, nombre: str) -> EstadoPedido:
    estado = db.scalar(select(EstadoPedido).where(EstadoPedido.nombre == nombre))
    if not estado:
        raise HTTPException(422, f"Estado '{nombre}' no existe")
    return estado


def obtener_pedido(db: Session, pedido_id: uuid.UUID, bloquear: bool = False) -> Pedido:
    """Carga un pedido. Con `bloquear=True` toma un bloqueo de fila (SELECT ... FOR UPDATE) hasta el commit.

    Toda operación que MODIFIQUE el pedido (editar, cambiar de estado, cancelar) debe bloquearlo: sin eso, dos usuarios
    simultáneos leen el mismo estado, ambos validan la transición contra él y ambos escriben (p. ej. «Enviado» y
    «Cancelado» a la vez). Con el bloqueo, el segundo espera, vuelve a leer el estado ya cambiado y su transición se
    valida contra la realidad. En SQLite (solo desarrollo) el bloqueo no existe.
    """
    consulta = select(Pedido).where(Pedido.pedido_id == pedido_id)
    if bloquear:
        # El estado se carga DESPUÉS del bloqueo (carga diferida), no con un JOIN: cuando una transacción espera el bloqueo,
        # PostgreSQL vuelve a evaluar la fila ya modificada y, con el JOIN, devolvía el pedido sin su estado.
        consulta = consulta.options(lazyload(Pedido.estado)).with_for_update()
    pedido = db.scalars(consulta).first()
    if not pedido:
        raise HTTPException(404, "Pedido no encontrado")
    return pedido


def _consolidar(items: list[ItemIn]) -> "OrderedDict[uuid.UUID, int]":
    """Une líneas repetidas del mismo producto sumando cantidades."""
    out: OrderedDict[uuid.UUID, int] = OrderedDict()
    for it in items:
        out[it.producto_id] = out.get(it.producto_id, 0) + it.cantidad
    return out


def _construir_detalles(catalogo: CatalogoClient, items: list[ItemIn]) -> list[DetallePedido]:
    detalles: list[DetallePedido] = []
    for producto_id, cantidad in _consolidar(items).items():
        prod = catalogo.obtener_producto(producto_id)
        if not prod:
            raise HTTPException(422, f"Producto {producto_id} no existe en el catálogo")
        if not prod["activo"]:
            raise HTTPException(422, f"Producto '{prod['nombre']}' no está activo")
        if prod["disponible"] < cantidad:
            raise HTTPException(
                409,
                f"Disponibilidad insuficiente para '{prod['nombre']}': "
                f"solicitado {cantidad}, disponible {prod['disponible']}",
            )
        # El precio SIEMPRE se toma del catálogo, nunca del cliente HTTP.
        d = DetallePedido(producto_id=producto_id, cantidad=cantidad, precio_unitario=prod["precio"], subtotal=0)
        d.calcular_subtotal()
        detalles.append(d)
    return detalles


def crear_pedido(
    db: Session, catalogo: CatalogoClient, vendedor: Vendedor, cliente_id: uuid.UUID, descripcion: str | None, items: list[ItemIn]
) -> Pedido:
    if not catalogo.obtener_cliente(cliente_id):
        raise HTTPException(422, f"Cliente {cliente_id} no existe en el catálogo")
    pedido = Pedido(
        cliente_id=cliente_id,
        vendedor_id=vendedor.vendedor_id,
        estado=obtener_estado(db, "Pendiente"),
        descripcion=descripcion,
    )
    pedido.detalles = _construir_detalles(catalogo, items)
    pedido.calcular_total(get_settings().iva_rate)
    db.add(pedido)
    db.flush()
    registrar_auditoria(
        db, pedido.pedido_id, vendedor.vendedor_id, "CREAR",
        f"Pedido creado con {len(pedido.detalles)} producto(s). Total {pedido.total}",
    )
    db.commit()
    db.refresh(pedido)
    return pedido


def modificar_pedido(
    db: Session, catalogo: CatalogoClient, vendedor: Vendedor, pedido: Pedido, descripcion: str | None, items: list[ItemIn] | None
) -> Pedido:
    if pedido.estado.nombre not in MODIFICABLES:
        raise HTTPException(409, f"No se puede modificar un pedido en estado '{pedido.estado.nombre}'")
    if descripcion is None and items is None:
        raise HTTPException(422, "Debe enviar descripcion o items para modificar")
    cambios: list[str] = []
    if descripcion is not None and descripcion != pedido.descripcion:
        pedido.descripcion = descripcion
        cambios.append("descripción actualizada")
    if items is not None:
        total_anterior = pedido.total
        pedido.detalles = _construir_detalles(catalogo, items)  # delete-orphan elimina los anteriores
        pedido.calcular_total(get_settings().iva_rate)
        cambios.append(f"productos reemplazados ({len(pedido.detalles)}); total {total_anterior} -> {pedido.total}")
    if not cambios:
        return pedido
    registrar_auditoria(db, pedido.pedido_id, vendedor.vendedor_id, "MODIFICAR", "; ".join(cambios))
    db.commit()
    db.refresh(pedido)
    return pedido


def cambiar_estado(db: Session, vendedor: Vendedor, pedido: Pedido, nuevo: str, comentario: str | None) -> Pedido:
    actual = pedido.estado.nombre
    if nuevo not in TRANSICIONES:
        raise HTTPException(422, f"Estado '{nuevo}' no existe")
    if nuevo not in TRANSICIONES[actual]:
        permitidos = ", ".join(sorted(TRANSICIONES[actual])) or "ninguno (estado final)"
        raise HTTPException(409, f"Transición no permitida: {actual} -> {nuevo}. Permitidos: {permitidos}")
    pedido.estado = obtener_estado(db, nuevo)
    detalle = f"{actual} -> {nuevo}" + (f". {comentario}" if comentario else "")
    registrar_auditoria(db, pedido.pedido_id, vendedor.vendedor_id, "CAMBIO_ESTADO", detalle)
    db.commit()
    db.refresh(pedido)
    return pedido


def cancelar_pedido(db: Session, vendedor: Vendedor, pedido: Pedido, motivo: str) -> Pedido:
    actual = pedido.estado.nombre
    if "Cancelado" not in TRANSICIONES[actual]:
        raise HTTPException(409, f"No se puede cancelar un pedido en estado '{actual}'")
    pedido.estado = obtener_estado(db, "Cancelado")
    registrar_auditoria(db, pedido.pedido_id, vendedor.vendedor_id, "CANCELAR", f"{actual} -> Cancelado. Motivo: {motivo}")
    db.commit()
    db.refresh(pedido)
    return pedido

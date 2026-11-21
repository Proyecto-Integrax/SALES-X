"""Modelo de datos de SALES-X.

Refleja el modelo entidad-relación y el diagrama de clases de la documentación:
ESTADO_PEDIDO, PEDIDO, DETALLE_PEDIDO, AUDITORIA_PEDIDO y VENDEDOR.
`cliente_id` y `producto_id` son identificadores comunes de INTEGRAX. CLIENTE y PRODUCTO son
copias locales (se sincronizan desde el catálogo de INTEGRAX) para poder tener integridad referencial (FK).
"""

import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from .database import Base

CENT = Decimal("0.01")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def money(value: Decimal | float | int) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


class Vendedor(Base):
    __tablename__ = "vendedor"

    vendedor_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    contrasena: Mapped[str] = mapped_column(String(100), nullable=False)  # hash bcrypt
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="vendedor")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # True = debe definir una contraseña propia antes de operar (usuario nuevo o contraseña restablecida)
    debe_cambiar_contrasena: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=expression.false()
    )

    __table_args__ = (CheckConstraint("rol IN ('admin','vendedor')", name="ck_vendedor_rol"),)


class EstadoPedido(Base):
    __tablename__ = "estado_pedido"

    estado_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(200))


class Cliente(Base):
    """Copia local del cliente (el dueño del dato es el microproyecto de Clientes)."""

    __tablename__ = "cliente"

    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(40), index=True)
    correo: Mapped[str | None] = mapped_column(String(160))
    fecha_sincronizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class Producto(Base):
    """Copia local del producto (el dueño del dato es el microproyecto de Productos/Inventario)."""

    __tablename__ = "producto"

    producto_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(40), index=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    disponible: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_sincronizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class Pedido(Base):
    __tablename__ = "pedido"

    pedido_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cliente.cliente_id"), nullable=False, index=True)
    estado_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("estado_pedido.estado_id"), nullable=False)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendedor.vendedor_id"), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    impuestos: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    descripcion: Mapped[str | None] = mapped_column(String(500))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    estado: Mapped[EstadoPedido] = relationship(lazy="joined")
    detalles: Mapped[list["DetallePedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin", order_by="DetallePedido.detalle_pedido_id"
    )

    __table_args__ = (
        Index("ix_pedido_fecha", "fecha_creacion"),
        Index("ix_pedido_estado", "estado_id"),
        CheckConstraint("total >= 0", name="ck_pedido_total"),
    )

    @property
    def estado_nombre(self) -> str:
        return self.estado.nombre

    def calcular_total(self, iva_rate: float) -> None:
        """Calcula subtotal, impuestos y total a partir de los detalles."""
        self.subtotal = money(sum((d.subtotal for d in self.detalles), Decimal("0")))
        self.impuestos = money(self.subtotal * Decimal(str(iva_rate)))
        self.total = money(self.subtotal + self.impuestos)


class DetallePedido(Base):
    __tablename__ = "detalle_pedido"

    detalle_pedido_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pedido.pedido_id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("producto.producto_id"), nullable=False, index=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    pedido: Mapped[Pedido] = relationship(back_populates="detalles")

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalle_cantidad"),
        CheckConstraint("precio_unitario >= 0", name="ck_detalle_precio"),
    )

    def calcular_subtotal(self) -> None:
        self.subtotal = money(self.precio_unitario * self.cantidad)


class AuditoriaPedido(Base):
    __tablename__ = "auditoria_pedido"

    auditoria_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pedido.pedido_id", ondelete="CASCADE"), nullable=False, index=True)
    # Nulo cuando la acción proviene de un sistema/cliente externo (solicitudes por integración).
    vendedor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendedor.vendedor_id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    descripcion: Mapped[str | None] = mapped_column(Text)
    accion: Mapped[str] = mapped_column(String(40), nullable=False)

    vendedor: Mapped[Vendedor | None] = relationship(lazy="joined")

    @property
    def usuario(self) -> str:
        return self.vendedor.nombre if self.vendedor else "Sistema externo"


class IntentoLogin(Base):
    """Fallos de inicio de sesión (bloqueo compartido entre instancias y reinicios)."""

    __tablename__ = "intento_login"

    intento_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    clave: Mapped[str] = mapped_column(String(170), nullable=False, index=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)


class ConsumidorApi(Base):
    """Sistema consumidor de los servicios de integración, con su propia clave."""

    __tablename__ = "consumidor_api"

    consumidor_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    clave_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # SHA-256 hex
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expira: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    ultimo_uso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

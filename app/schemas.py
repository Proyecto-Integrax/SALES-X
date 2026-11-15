import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .security import validar_contrasena


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------- Autenticación / usuarios ----------
class LoginIn(BaseModel):
    correo: str = Field(min_length=3, max_length=160)
    contrasena: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class VendedorOut(ORM):
    vendedor_id: uuid.UUID
    nombre: str
    correo: str
    rol: str
    activo: bool
    debe_cambiar_contrasena: bool = False


class VendedorCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    correo: str = Field(min_length=5, max_length=160, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    contrasena: str = Field(min_length=10, max_length=128)
    rol: Literal["admin", "vendedor"] = "vendedor"

    @model_validator(mode="after")
    def _politica(self):
        validar_contrasena(self.contrasena, self.correo)
        return self


class VendedorUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    rol: Literal["admin", "vendedor"] | None = None
    activo: bool | None = None
    contrasena: str | None = Field(default=None, min_length=10, max_length=128)

    @field_validator("contrasena")
    @classmethod
    def _politica(cls, v):
        return validar_contrasena(v) if v is not None else v


class CambiarContrasenaIn(BaseModel):
    actual: str = Field(min_length=1, max_length=128)
    nueva: str = Field(min_length=10, max_length=128)

    @field_validator("nueva")
    @classmethod
    def _politica(cls, v):
        return validar_contrasena(v)


# ---------- Consumidores de integración ----------
class ConsumidorCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=80)
    expira: datetime | None = None


class ConsumidorUpdate(BaseModel):
    activo: bool | None = None
    expira: datetime | None = None
    sin_expiracion: bool = False


class ConsumidorOut(ORM):
    consumidor_id: uuid.UUID
    nombre: str
    activo: bool
    expira: datetime | None
    creado: datetime
    ultimo_uso: datetime | None


class ConsumidorCreado(ConsumidorOut):
    clave: str  # se muestra UNA sola vez


# ---------- Catálogo (INTEGRAX) ----------
class ClienteOut(BaseModel):
    cliente_id: uuid.UUID
    nombre: str
    documento: str | None = None
    correo: str | None = None


class ProductoOut(BaseModel):
    producto_id: uuid.UUID
    nombre: str
    sku: str | None = None
    precio: Decimal
    disponible: int
    activo: bool = True


class DisponibilidadOut(BaseModel):
    producto_id: uuid.UUID
    nombre: str
    disponible: int
    activo: bool


# ---------- Pedidos ----------
class ItemIn(BaseModel):
    producto_id: uuid.UUID
    cantidad: int = Field(gt=0, le=10000)


class PedidoCreate(BaseModel):
    cliente_id: uuid.UUID
    descripcion: str | None = Field(default=None, max_length=500)
    items: list[ItemIn] = Field(min_length=1, max_length=100)


class PedidoUpdate(BaseModel):
    descripcion: str | None = Field(default=None, max_length=500)
    items: list[ItemIn] | None = Field(default=None, min_length=1, max_length=100)


class EstadoChange(BaseModel):
    estado: str = Field(min_length=3, max_length=40)
    comentario: str | None = Field(default=None, max_length=300)


class CancelarIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=300)


class DetalleOut(ORM):
    detalle_pedido_id: uuid.UUID
    producto_id: uuid.UUID
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class PedidoOut(ORM):
    pedido_id: uuid.UUID
    cliente_id: uuid.UUID
    estado_id: uuid.UUID
    estado: str = Field(validation_alias="estado_nombre")
    vendedor_id: uuid.UUID
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal
    descripcion: str | None
    fecha_creacion: datetime
    detalles: list[DetalleOut]


class PedidoResumen(ORM):
    pedido_id: uuid.UUID
    cliente_id: uuid.UUID
    estado: str = Field(validation_alias="estado_nombre")
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal
    fecha_creacion: datetime


class Page(BaseModel):
    items: list[PedidoResumen]
    total: int
    page: int
    size: int


class EstadoOut(ORM):
    estado_id: uuid.UUID
    nombre: str
    descripcion: str | None


class AuditoriaOut(ORM):
    auditoria_id: uuid.UUID
    pedido_id: uuid.UUID
    accion: str
    descripcion: str | None
    fecha: datetime
    usuario: str


class HistorialCliente(BaseModel):
    cliente_id: uuid.UUID
    total_pedidos: int
    total_comprado: Decimal
    pedidos: list[PedidoResumen]


# ---------- Integración ----------
class SolicitudIn(BaseModel):
    tipo: Literal["modificacion", "cancelacion"]
    detalle: str = Field(min_length=3, max_length=500)
    solicitante: str | None = Field(default=None, max_length=120)


class SolicitudOut(BaseModel):
    pedido_id: uuid.UUID
    tipo: str
    estado: str = "RECIBIDA"
    mensaje: str


# ---------- Reportes ----------
class PeriodoVentas(BaseModel):
    periodo: str
    pedidos: int
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal


class ReporteVentas(BaseModel):
    desde: date | None
    hasta: date | None
    agrupar: str
    total_pedidos: int
    pedidos_cancelados: int
    subtotal: Decimal
    impuestos: Decimal
    total_ventas: Decimal
    ticket_promedio: Decimal
    por_estado: dict[str, int]
    serie: list[PeriodoVentas]
    generado: datetime

"""Datos iniciales idempotentes: estados de pedido y usuarios."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import ConsumidorApi, EstadoPedido, Vendedor
from .security import hash_api_key, hash_password
from .services.pedidos import ESTADOS


def seed(db: Session) -> None:
    s = get_settings()
    existentes = {e.nombre for e in db.scalars(select(EstadoPedido)).all()}
    for nombre, desc in ESTADOS:
        if nombre not in existentes:
            db.add(EstadoPedido(nombre=nombre, descripcion=desc))

    def ensure(nombre: str, correo: str, password: str, rol: str) -> None:
        if not db.scalar(select(Vendedor).where(Vendedor.correo == correo.lower())):
            db.add(Vendedor(nombre=nombre, correo=correo.lower(), contrasena=hash_password(password), rol=rol))

    # Consumidor inicial de integración a partir de INTEGRATION_API_KEY (solo si no existe ninguno)
    if not db.scalar(select(ConsumidorApi).limit(1)):
        db.add(ConsumidorApi(nombre="INTEGRAX-inicial", clave_hash=hash_api_key(s.integration_api_key)))

    ensure(s.admin_name, s.admin_email, s.admin_password, "admin")
    if s.seed_demo_users:
        ensure("Vendedor Demo", "vendedor@salesx.local", "Ventas2026*", "vendedor")
    db.commit()

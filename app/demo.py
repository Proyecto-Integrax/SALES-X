"""Genera pedidos de demostración (últimos 30 días) para probar panel y reportes.

Uso:  python -m app.demo          (no hace nada si ya existen pedidos)
      python -m app.demo --force  (agrega los pedidos de todas formas)
"""

import random
import sys
from datetime import timedelta

from sqlalchemy import func, select

from .database import Base, SessionLocal, engine
from .integration.catalogo import get_catalogo
from .models import AuditoriaPedido, Pedido, Vendedor, utcnow
from .schemas import ItemIn
from .seed import seed
from .services import pedidos as svc


def main(force: bool = False, cantidad: int = 40) -> None:
    Base.metadata.create_all(engine)
    rnd = random.Random(2026)
    cat = get_catalogo()
    with SessionLocal() as db:
        seed(db)
        if db.scalar(select(func.count()).select_from(Pedido)) and not force:
            print("Ya existen pedidos; use --force para agregar datos de demostración.")
            return
        vendedores = db.scalars(select(Vendedor).where(Vendedor.activo)).all()
        clientes = cat.listar_clientes()
        productos = [p for p in cat.listar_productos() if p["activo"] and p["disponible"] > 5]
        for _ in range(cantidad):
            v = rnd.choice(vendedores)
            items = [ItemIn(producto_id=p["producto_id"], cantidad=rnd.randint(1, 4)) for p in rnd.sample(productos, rnd.randint(1, 3))]
            ped = svc.crear_pedido(db, cat, v, rnd.choice(clientes)["cliente_id"], rnd.choice([None, "Entrega en bodega", "Cliente frecuente", "Urgente"]), items)
            destino = rnd.choices(["Pendiente", "Confirmado", "En preparación", "Enviado", "Entregado", "Cancelado"], [2, 2, 2, 2, 6, 1])[0]
            if destino == "Cancelado":
                svc.cancelar_pedido(db, v, ped, "Cliente desistió de la compra")
            else:
                for e in ["Confirmado", "En preparación", "Enviado", "Entregado"]:
                    if destino == "Pendiente":
                        break
                    svc.cambiar_estado(db, v, ped, e, None)
                    if e == destino:
                        break
            # Reparte las fechas en los últimos 30 días (pedido y su auditoría coherentes)
            atras = timedelta(days=rnd.randint(0, 29), hours=rnd.randint(0, 9), minutes=rnd.randint(0, 59))
            ped.fecha_creacion = utcnow() - atras
            for i, a in enumerate(db.scalars(select(AuditoriaPedido).where(AuditoriaPedido.pedido_id == ped.pedido_id).order_by(AuditoriaPedido.fecha)).all()):
                a.fecha = ped.fecha_creacion + timedelta(minutes=15 * i)
            db.commit()
        print(f"Se generaron {cantidad} pedidos de demostración.")


if __name__ == "__main__":
    main(force="--force" in sys.argv)

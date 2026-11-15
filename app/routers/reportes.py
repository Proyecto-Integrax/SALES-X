import csv
import io
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import current_user
from ..models import Pedido, money
from ..schemas import PeriodoVentas, ReporteVentas
from ..timeutil import day_end, day_start, to_local

router = APIRouter(prefix="/reportes", tags=["Reportes"], dependencies=[Depends(current_user)])


def _construir(db: Session, desde: date | None, hasta: date | None, agrupar: str) -> ReporteVentas:
    conds = []
    if desde:
        conds.append(Pedido.fecha_creacion >= day_start(desde))
    if hasta:
        conds.append(Pedido.fecha_creacion <= day_end(hasta))
    pedidos = db.scalars(select(Pedido).where(*conds).order_by(Pedido.fecha_creacion)).all()

    por_estado: dict[str, int] = defaultdict(int)
    serie: "OrderedDict[str, list[Decimal | int]]" = OrderedDict()
    sub = imp = tot = Decimal("0")
    vendidos = 0
    for p in pedidos:
        por_estado[p.estado.nombre] += 1
        if p.estado.nombre == "Cancelado":  # las ventas excluyen pedidos cancelados
            continue
        vendidos += 1
        sub += p.subtotal
        imp += p.impuestos
        tot += p.total
        clave = to_local(p.fecha_creacion).strftime("%Y-%m" if agrupar == "mes" else "%Y-%m-%d")
        fila = serie.setdefault(clave, [0, Decimal("0"), Decimal("0"), Decimal("0")])
        fila[0] += 1
        fila[1] += p.subtotal
        fila[2] += p.impuestos
        fila[3] += p.total

    return ReporteVentas(
        desde=desde,
        hasta=hasta,
        agrupar=agrupar,
        total_pedidos=len(pedidos),
        pedidos_cancelados=por_estado.get("Cancelado", 0),
        subtotal=money(sub),
        impuestos=money(imp),
        total_ventas=money(tot),
        ticket_promedio=money(tot / vendidos) if vendidos else Decimal("0.00"),
        por_estado=dict(por_estado),
        serie=[PeriodoVentas(periodo=k, pedidos=v[0], subtotal=v[1], impuestos=v[2], total=v[3]) for k, v in serie.items()],
        generado=datetime.now(timezone.utc),
    )


@router.get("/ventas", response_model=ReporteVentas, summary="Reporte de ventas (RF-10)")
def ventas(
    desde: date | None = None,
    hasta: date | None = None,
    agrupar: Literal["dia", "mes"] = "dia",
    db: Session = Depends(get_db),
):
    return _construir(db, desde, hasta, agrupar)


@router.get("/ventas.csv", summary="Reporte de ventas en CSV")
def ventas_csv(
    desde: date | None = None,
    hasta: date | None = None,
    agrupar: Literal["dia", "mes"] = "dia",
    db: Session = Depends(get_db),
):
    r = _construir(db, desde, hasta, agrupar)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["periodo", "pedidos", "subtotal", "impuestos", "total"])
    for f in r.serie:
        w.writerow([f.periodo, f.pedidos, f.subtotal, f.impuestos, f.total])
    w.writerow(["TOTAL", sum(f.pedidos for f in r.serie), r.subtotal, r.impuestos, r.total_ventas])
    return Response(
        content="﻿" + buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="reporte_ventas.csv"'},
    )

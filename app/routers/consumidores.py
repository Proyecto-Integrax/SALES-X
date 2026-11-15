"""Administración de consumidores de integración y sus claves (REQ-15)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import ConsumidorApi, utcnow
from ..schemas import ConsumidorCreado, ConsumidorCreate, ConsumidorOut, ConsumidorUpdate
from ..security import generate_api_key, hash_api_key
from ..timeutil import as_utc

router = APIRouter(prefix="/consumidores", tags=["Consumidores de integración (admin)"], dependencies=[Depends(require_admin)])


def _futuro(expira):
    if expira is not None and as_utc(expira) <= utcnow():
        raise HTTPException(422, "La fecha de expiración debe ser futura")


@router.get("", response_model=list[ConsumidorOut], summary="Listar consumidores")
def listar(db: Session = Depends(get_db)):
    return db.scalars(select(ConsumidorApi).order_by(ConsumidorApi.nombre)).all()


@router.post("", response_model=ConsumidorCreado, status_code=201, summary="Crear consumidor (la clave se muestra una sola vez)")
def crear(data: ConsumidorCreate, db: Session = Depends(get_db)):
    _futuro(data.expira)
    if db.scalar(select(ConsumidorApi).where(ConsumidorApi.nombre == data.nombre)):
        raise HTTPException(409, "Ya existe un consumidor con ese nombre")
    clave = generate_api_key()
    c = ConsumidorApi(nombre=data.nombre, clave_hash=hash_api_key(clave), expira=data.expira)
    db.add(c)
    db.commit()
    return ConsumidorCreado(**ConsumidorOut.model_validate(c).model_dump(), clave=clave)


@router.patch("/{consumidor_id}", response_model=ConsumidorOut, summary="Activar/desactivar o cambiar expiración")
def actualizar(consumidor_id: uuid.UUID, data: ConsumidorUpdate, db: Session = Depends(get_db)):
    c = db.get(ConsumidorApi, consumidor_id)
    if not c:
        raise HTTPException(404, "Consumidor no encontrado")
    if data.activo is not None:
        c.activo = data.activo
    if data.sin_expiracion:
        c.expira = None
    elif data.expira is not None:
        _futuro(data.expira)
        c.expira = data.expira
    db.commit()
    return c

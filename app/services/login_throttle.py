"""Bloqueo por intentos fallidos, persistido en la base de datos (REQ-14).

Compartido entre todas las instancias de la API y vigente tras reinicios.
"""

from datetime import timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import IntentoLogin, utcnow

MAX_INTENTOS = 5
VENTANA = timedelta(minutes=5)


def _clave(clave: str) -> str:
    return clave[:170]


def bloqueado(db: Session, clave: str) -> bool:
    desde = utcnow() - VENTANA
    n = db.scalar(select(func.count()).select_from(IntentoLogin).where(IntentoLogin.clave == _clave(clave), IntentoLogin.fecha >= desde))
    return (n or 0) >= MAX_INTENTOS


def registrar_fallo(db: Session, clave: str) -> None:
    db.add(IntentoLogin(clave=_clave(clave)))
    db.execute(delete(IntentoLogin).where(IntentoLogin.fecha < utcnow() - 2 * VENTANA))  # limpieza de filas viejas
    db.commit()


def limpiar(db: Session, clave: str) -> None:
    db.execute(delete(IntentoLogin).where(IntentoLogin.clave == _clave(clave)))
    db.commit()

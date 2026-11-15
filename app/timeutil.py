"""Zona horaria de negocio: las fechas se guardan en UTC pero los filtros y
agrupaciones de reportes se interpretan en la zona del negocio (BUSINESS_TZ)."""

from datetime import date, datetime, time, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from .config import get_settings


@lru_cache
def tz() -> ZoneInfo:
    return ZoneInfo(get_settings().business_tz)


def day_start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=tz()).astimezone(timezone.utc)


def day_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=tz()).astimezone(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    """Marca como UTC una fecha sin zona (SQLite) o la convierte a UTC."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def to_local(dt: datetime) -> datetime:
    """Convierte una fecha de la BD (SQLite la devuelve sin zona = UTC) a hora local de negocio."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz())

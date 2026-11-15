import secrets
import uuid

import jwt
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import ConsumidorApi, Vendedor, utcnow
from .security import decode_access_token, hash_api_key
from .timeutil import as_utc

SESSION_COOKIE = "salesx_session"
CSRF_COOKIE = "salesx_csrf"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

bearer = HTTPBearer(auto_error=False)


def session_user(
    request: Request, cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> Vendedor:
    """Usuario autenticado (cabecera Bearer o cookie de sesión). No aplica el cambio obligatorio de contraseña."""
    unauthorized = HTTPException(401, "Credenciales inválidas o sesión expirada", headers={"WWW-Authenticate": "Bearer"})
    if cred:
        token = cred.credentials  # los clientes de API no usan cookies → sin riesgo CSRF
    else:
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            raise unauthorized
        if request.method not in SAFE_METHODS:  # CSRF "double submit": cabecera = cookie
            header, cookie = request.headers.get("x-csrf-token"), request.cookies.get(CSRF_COOKIE)
            if not header or not cookie or not secrets.compare_digest(header.encode(), cookie.encode()):
                raise HTTPException(403, "Token CSRF inválido o ausente")
    try:
        payload = decode_access_token(token)
        user = db.get(Vendedor, uuid.UUID(payload["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise unauthorized
    if not user or not user.activo:
        raise unauthorized
    return user


def current_user(user: Vendedor = Depends(session_user)) -> Vendedor:
    if user.debe_cambiar_contrasena:
        raise HTTPException(403, "Debe cambiar su contraseña antes de continuar")
    return user


def require_admin(user: Vendedor = Depends(current_user)) -> Vendedor:
    if user.rol != "admin":
        raise HTTPException(403, "Se requiere rol administrador")
    return user


def require_api_key(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)) -> ConsumidorApi:
    invalid = HTTPException(401, "API Key de integración inválida, inactiva o expirada")
    if not x_api_key:
        raise invalid
    consumidor = db.scalar(select(ConsumidorApi).where(ConsumidorApi.clave_hash == hash_api_key(x_api_key)))
    ahora = utcnow()
    if not consumidor or not consumidor.activo or (consumidor.expira and as_utc(consumidor.expira) <= ahora):
        raise invalid
    consumidor.ultimo_uso = ahora
    db.commit()
    return consumidor

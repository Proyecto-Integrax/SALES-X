import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import CSRF_COOKIE, SESSION_COOKIE, current_user, require_admin, session_user
from ..models import Vendedor
from ..schemas import CambiarContrasenaIn, LoginIn, TokenOut, VendedorCreate, VendedorOut, VendedorUpdate
from ..security import create_access_token, hash_password, verify_password
from ..services import login_throttle

router = APIRouter(tags=["Autenticación y usuarios"])

# Hash ficticio para igualar tiempos de respuesta cuando el correo no existe.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def _cookie_args(max_age: int) -> dict:
    return {"max_age": max_age, "samesite": "strict", "secure": get_settings().environment == "production", "path": "/"}


@router.post("/auth/login", response_model=TokenOut, summary="Iniciar sesión")
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    """Devuelve el JWT (para clientes de API) y además fija la sesión en cookie HttpOnly + cookie CSRF."""
    key = data.correo.strip().lower()
    if login_throttle.bloqueado(db, key):
        raise HTTPException(429, "Demasiados intentos fallidos. Intente de nuevo en 5 minutos.")
    user = db.scalar(select(Vendedor).where(Vendedor.correo == key))
    ok = verify_password(data.contrasena, user.contrasena if user else _DUMMY_HASH)
    if not user or not ok or not user.activo:
        login_throttle.registrar_fallo(db, key)
        raise HTTPException(401, "Correo o contraseña incorrectos")
    login_throttle.limpiar(db, key)
    token, expires = create_access_token(user.vendedor_id, user.rol)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, **_cookie_args(expires))
    response.set_cookie(CSRF_COOKIE, secrets.token_urlsafe(32), httponly=False, **_cookie_args(expires))
    return TokenOut(access_token=token, expires_in=expires)


@router.post("/auth/logout", status_code=204, summary="Cerrar sesión (elimina las cookies)")
def logout():
    resp = Response(status_code=204)
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        resp.delete_cookie(name, path="/")
    return resp


@router.get("/auth/me", response_model=VendedorOut, summary="Usuario autenticado")
def me(user: Vendedor = Depends(session_user)):
    return user


@router.post("/auth/cambiar-contrasena", status_code=204, summary="Cambiar la propia contraseña (REQ-17)")
def cambiar_contrasena(data: CambiarContrasenaIn, db: Session = Depends(get_db), user: Vendedor = Depends(session_user)):
    key = f"pw:{user.correo}"
    if login_throttle.bloqueado(db, key):
        raise HTTPException(429, "Demasiados intentos fallidos. Intente de nuevo en 5 minutos.")
    if not verify_password(data.actual, user.contrasena):
        login_throttle.registrar_fallo(db, key)
        raise HTTPException(400, "La contraseña actual es incorrecta")
    if data.nueva == data.actual:
        raise HTTPException(422, "La nueva contraseña debe ser distinta de la actual")
    local = user.correo.split("@")[0].lower()
    if len(local) >= 4 and local in data.nueva.lower():
        raise HTTPException(422, "La contraseña no debe contener su usuario")
    user.contrasena = hash_password(data.nueva)
    user.debe_cambiar_contrasena = False
    db.commit()
    login_throttle.limpiar(db, key)
    return Response(status_code=204)


@router.get("/vendedores", response_model=list[VendedorOut], summary="Listar usuarios (admin)")
def listar(db: Session = Depends(get_db), _: Vendedor = Depends(require_admin)):
    return db.scalars(select(Vendedor).order_by(Vendedor.nombre)).all()


@router.post("/vendedores", response_model=VendedorOut, status_code=201, summary="Crear usuario (admin)")
def crear(data: VendedorCreate, db: Session = Depends(get_db), _: Vendedor = Depends(require_admin)):
    correo = data.correo.strip().lower()
    if db.scalar(select(Vendedor).where(Vendedor.correo == correo)):
        raise HTTPException(409, "Ya existe un usuario con ese correo")
    user = Vendedor(
        nombre=data.nombre, correo=correo, contrasena=hash_password(data.contrasena), rol=data.rol,
        debe_cambiar_contrasena=True,  # la contraseña inicial la conoce el administrador: debe cambiarla
    )
    db.add(user)
    db.commit()
    return user


@router.patch("/vendedores/{vendedor_id}", response_model=VendedorOut, summary="Actualizar usuario (admin)")
def actualizar(
    vendedor_id: str, data: VendedorUpdate, db: Session = Depends(get_db), admin: Vendedor = Depends(require_admin)
):
    try:
        vid = uuid.UUID(vendedor_id)
    except ValueError:
        raise HTTPException(422, "Identificador inválido")
    user = db.get(Vendedor, vid)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    if user.vendedor_id == admin.vendedor_id and (data.activo is False or (data.rol and data.rol != "admin")):
        raise HTTPException(409, "No puede desactivarse ni quitarse el rol a sí mismo")
    if data.nombre is not None:
        user.nombre = data.nombre
    if data.rol is not None:
        user.rol = data.rol
    if data.activo is not None:
        user.activo = data.activo
    if data.contrasena is not None:
        user.contrasena = hash_password(data.contrasena)
        user.debe_cambiar_contrasena = user.vendedor_id != admin.vendedor_id  # restablecer a otro → debe cambiarla
    db.commit()
    return user

import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import get_settings

ALGORITHM = "HS256"


# ---------- Contraseñas ----------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


_COMUNES = {"password123", "contrasena123", "qwerty12345", "admin12345", "bienvenido1", "colombia123", "12345678ab"}


def validar_contrasena(password: str, correo: str | None = None) -> str:
    """Política: ≥10 caracteres, letras y números, no común, sin la parte local del correo."""
    if len(password) < 10:
        raise ValueError("La contraseña debe tener al menos 10 caracteres")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("La contraseña debe incluir letras y números")
    if password.lower() in _COMUNES:
        raise ValueError("La contraseña es demasiado común")
    if correo:
        local = correo.split("@")[0].lower()
        if len(local) >= 4 and local in password.lower():
            raise ValueError("La contraseña no debe contener su usuario")
    return password


# ---------- Tokens de sesión ----------
def create_access_token(vendedor_id: uuid.UUID, rol: str) -> tuple[str, int]:
    s = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=s.token_expire_minutes)
    token = jwt.encode({"sub": str(vendedor_id), "rol": rol, "exp": expires}, s.secret_key, algorithm=ALGORITHM)
    return token, s.token_expire_minutes * 60


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])


# ---------- Claves de integración ----------
def generate_api_key() -> str:
    """Clave aleatoria de alta entropía (256 bits); por eso basta un hash rápido para almacenarla."""
    return "sx_" + secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

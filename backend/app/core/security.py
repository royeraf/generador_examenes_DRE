import bcrypt
import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional
from jose import JWTError, jwt
from starlette.concurrency import run_in_threadpool
from app.core.config import get_settings

settings = get_settings()

# Coste de bcrypt. 12 rondas cuestan ~342 ms por verificación en el VPS de
# producción: con 2 workers eso limita el login a ~3 por segundo y bloquea el
# event loop. 10 rondas (~85 ms) sigue siendo un coste recomendado por OWASP y
# multiplica por 4 la capacidad. Los hashes antiguos se re-hashean solos en el
# siguiente login exitoso (ver needs_rehash).
BCRYPT_ROUNDS = max(4, min(16, int(os.getenv("BCRYPT_ROUNDS", "10"))))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token. Incluye un jti único para rastrear la sesión."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    if "jti" not in to_encode:
        to_encode["jti"] = uuid.uuid4().hex
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    """Hash password."""
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """bcrypt en el threadpool para no bloquear el event loop.

    bcrypt es CPU-bound (~85-340 ms). Llamarlo directamente desde una corrutina
    detiene el worker completo de uvicorn: ninguna otra petición de ese worker
    avanza mientras se verifica la contraseña. Con 2 workers, un aula entrando
    a la vez serializa el login de toda la región.
    """
    return await run_in_threadpool(verify_password, plain_password, hashed_password)


async def get_password_hash_async(password: str) -> str:
    """bcrypt en el threadpool (mismo motivo que verify_password_async)."""
    return await run_in_threadpool(get_password_hash, password)


def needs_rehash(hashed_password: str) -> bool:
    """True si el hash guardado no usa el coste actual (BCRYPT_ROUNDS).

    Permite migrar los hashes viejos (rounds 12) a 10 de forma transparente en
    el siguiente login exitoso, sin invalidar contraseñas ni pedir cambios.
    """
    try:
        return int(hashed_password.split("$")[2]) != BCRYPT_ROUNDS
    except (IndexError, ValueError):
        return False


@lru_cache(maxsize=1)
def get_dummy_hash() -> str:
    """Hash de descarte con el mismo costo de bcrypt.

    Se usa cuando el identificador no existe para que el tiempo de respuesta
    del login no delate qué cuentas están registradas (anti timing attack).
    """
    return get_password_hash("timing-equalizer-not-a-real-password")

"""Protección anti fuerza bruta para el login.

Reutiliza la tabla ``sesiones_acceso`` (donde ya se auditan los intentos
fallidos) para bloquear temporalmente un origen que acumula demasiados
errores de credenciales.

Se aplican dos límites independientes:
- por IP + identificador: evita atacar una cuenta concreta.
- por IP: evita barrer muchos identificadores desde un mismo origen.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.sesion import SesionAcceso

settings = get_settings()


@dataclass(frozen=True)
class LoginThrottle:
    """Resultado de la comprobación de bloqueo del login."""

    blocked: bool
    retry_after: int = 0


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normaliza a UTC los datetimes que algunos motores devuelven sin tzinfo."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def _failed_stats(
    db: AsyncSession, *conditions
) -> tuple[int, Optional[datetime]]:
    """Cuenta intentos fallidos y devuelve el más reciente de ellos."""
    result = await db.execute(
        select(
            func.count(SesionAcceso.id),
            func.max(SesionAcceso.login_at),
        ).where(*conditions)
    )
    count, last = result.one()
    return int(count or 0), _as_utc(last)


def _retry_seconds(
    last: Optional[datetime], now: datetime, window: timedelta
) -> int:
    """Segundos que faltan para que el intento más reciente salga de la ventana."""
    if last is None:
        return max(1, int(window.total_seconds()))
    return max(1, ceil((last + window - now).total_seconds()))


async def check_login_allowed(
    db: AsyncSession,
    ip: Optional[str],
    identifier: str,
) -> LoginThrottle:
    """Indica si el login debe bloquearse y cuántos segundos faltan.

    Solo cuenta intentos fallidos por credenciales dentro de la ventana
    configurada. Los intentos bloqueados no se registran, para que un atacante
    no pueda prolongar indefinidamente el bloqueo.
    """
    if settings.login_max_attempts <= 0 and settings.login_max_ip_attempts <= 0:
        return LoginThrottle(blocked=False)

    now = datetime.now(timezone.utc)
    window = timedelta(minutes=max(1, settings.login_attempt_window_minutes))
    since = now - window

    base_conditions = (
        SesionAcceso.exito.is_(False),
        SesionAcceso.motivo == "credenciales",
        SesionAcceso.login_at >= since,
    )

    ident = (identifier or "").strip().upper()
    retry_candidates: list[int] = []

    if ip:
        if settings.login_max_attempts > 0 and ident:
            count, last = await _failed_stats(
                db,
                *base_conditions,
                SesionAcceso.ip == ip,
                func.upper(SesionAcceso.identificador) == ident,
            )
            if count >= settings.login_max_attempts:
                retry_candidates.append(_retry_seconds(last, now, window))

        if settings.login_max_ip_attempts > 0:
            count_ip, last_ip = await _failed_stats(
                db,
                *base_conditions,
                SesionAcceso.ip == ip,
            )
            if count_ip >= settings.login_max_ip_attempts:
                retry_candidates.append(_retry_seconds(last_ip, now, window))
    elif ident and settings.login_max_attempts > 0:
        # Sin IP disponible solo se puede limitar por identificador.
        count, last = await _failed_stats(
            db,
            *base_conditions,
            func.upper(SesionAcceso.identificador) == ident,
        )
        if count >= settings.login_max_attempts:
            retry_candidates.append(_retry_seconds(last, now, window))

    if not retry_candidates:
        return LoginThrottle(blocked=False)

    return LoginThrottle(blocked=True, retry_after=max(1, max(retry_candidates)))

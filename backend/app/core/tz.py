"""Convención de fechas del sistema.

Toda columna datetime de negocio (ventana de asignación, intentos, progreso,
último acceso, expiración de códigos, fecha de creación) se guarda en **hora
Perú (America/Lima, UTC-5) y naive** (sin tzinfo), igual que la hace el motor
de BD con ``CURRENT_TIMESTAMP``.

Perú no aplica horario de verano, así que el offset es fijo -05 todo el año.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

TZ_PERU = timezone(timedelta(hours=-5))


def ahora_peru() -> datetime:
    """Ahora en hora Perú, naive — la forma exacta en que se persiste en BD."""
    return datetime.now(TZ_PERU).replace(tzinfo=None)


def a_peru_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Normaliza cualquier datetime a hora Perú naive.

    - naive → se asume que ya está en hora Perú y se devuelve tal cual.
    - aware → se convierte a America/Lima y se descarta el offset.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(TZ_PERU).replace(tzinfo=None)


def iso_peru(dt: Optional[datetime]) -> Optional[str]:
    """Serializa a ISO-8601 con offset ``-05:00``.

    El frontend parsea el string con ``new Date()``: con el offset explícito la
    hora Perú se conserva sea cual sea la zona del navegador.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_PERU)
    else:
        dt = dt.astimezone(TZ_PERU)
    return dt.isoformat()

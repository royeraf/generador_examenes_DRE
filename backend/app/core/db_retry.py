"""Reintento ante conflictos de concurrencia transitorios de MariaDB/MySQL.

IMPORTANTE — producción (VPS) usa tablas MyISAM, no InnoDB (ver `intentos_examen`,
`respuestas_intento`, `progreso_estudiante`). MyISAM no soporta SELECT ... FOR UPDATE
(se ignora silenciosamente) ni transacciones reales (no hay rollback: cada INSERT/
UPDATE que ya se envió al servidor es permanente aunque una sentencia posterior de la
misma "transacción" falle). Por eso los locks de este código son best-effort en local
(InnoDB) pero la protección real en producción viene de:
  1. Los UNIQUE KEY existentes (`uq_intento`, `uq_progreso_matricula_area`, etc.) +
     capturar el IntegrityError que producen y reintentar re-leyendo el estado actual.
  2. Sentencias UPDATE de una sola pasada con expresiones sobre columnas existentes
     (ej. `total = total + 1`) en vez de leer-en-Python-y-escribir — una sola sentencia
     SQL es atómica en el servidor independientemente del motor de almacenamiento.

Códigos MySQL/MariaDB reintentables:
  - 1062 ER_DUP_ENTRY: violación de UNIQUE KEY por un INSERT concurrente — el caso que
    realmente ocurre en producción (MyISAM), ya que ahí no hay locking que lo prevenga
    de antemano.
  - 1213 ER_LOCK_DEADLOCK (solo InnoDB): el gap lock no es exclusivo entre
    transacciones (dos pueden tomarlo a la vez) pero el INSERT posterior sí lo es, así
    que dos transacciones que toman el mismo gap y luego intentan insertar se
    deadlockean. Puede darse incluso entre estudiantes DISTINTOS que inician el mismo
    examen casi al mismo tiempo (el caso real de "toda la clase entra a las 8am").
  - 1020 ER_CHECKREAD (solo MariaDB con innodb_snapshot_isolation=ON): lock de lectura
    que colisiona con una fila modificada por otra transacción concurrente.
  - 1205 ER_LOCK_WAIT_TIMEOUT (solo InnoDB): se agotó innodb_lock_wait_timeout.

IMPORTANTE: fn() debe depender solo de datos planos capturados ANTES de llamar a
con_reintento (ids, no objetos ORM) además de sus propias queries. Un rollback()
expira TODOS los objetos ORM ya cargados en la sesión (current_user, filas ya
consultadas fuera del closure); volver a tocar sus atributos después dispara una
carga perezosa fuera de un contexto async-safe (sqlalchemy.exc.MissingGreenlet).
"""
import asyncio
import random
from typing import Awaitable, Callable, TypeVar

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

_ER_DUP_ENTRY = 1062
_CODIGOS_OPERATIONAL_REINTENTABLES = {1213, 1020, 1205}


def es_conflicto_reintentable(exc: BaseException) -> bool:
    orig = getattr(exc, "orig", None)
    args = getattr(orig, "args", None)
    if not args:
        return False
    if isinstance(exc, IntegrityError):
        return args[0] == _ER_DUP_ENTRY
    if isinstance(exc, OperationalError):
        return args[0] in _CODIGOS_OPERATIONAL_REINTENTABLES
    return False


async def con_reintento(db: AsyncSession, fn: Callable[[], Awaitable[T]], intentos: int = 5) -> T:
    """Ejecuta fn() reintentando ante conflictos de concurrencia (ver arriba),
    con un pequeño backoff aleatorio para no volver a colisionar en cadena."""
    for intento in range(intentos):
        try:
            return await fn()
        except (IntegrityError, OperationalError) as e:
            if es_conflicto_reintentable(e) and intento < intentos - 1:
                await db.rollback()
                await asyncio.sleep(random.uniform(0.02, 0.08) * (intento + 1))
                continue
            raise
    raise AssertionError("unreachable")

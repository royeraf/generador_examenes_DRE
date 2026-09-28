"""convertir fechas de negocio a hora peru

Las columnas datetime de negocio (ventana de asignación, intentos, progreso,
último acceso, expiración de códigos) se escribían en UTC desde Python, mientras
que fecha_creacion la escribía el motor de BD en su hora local: la tabla mezclaba
dos convenciones y al inspeccionarla no cuadraba.

Ahora todo se guarda en hora Perú (naive), así que hay que desplazar -5 h las
filas existentes que están en UTC. No se toca sesiones_acceso: la auditoría de
sesiones se mantiene en UTC (es un subsistema cerrado, sin fecha_creacion).

Revision ID: d7e8f9a0b1c2
Revises: b8c9d0e1f2a3
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect as sa_inspect


# revision identifiers, used by Alembic.
revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Escritas por Python en UTC -> siempre hay que convertirlas.
PYTHON_UTC = {
    'asignaciones_examen': ['fecha_inicio', 'fecha_fin'],
    'intentos_examen': ['fecha_inicio', 'fecha_fin'],
    'progreso_estudiante': ['ultima_actividad'],
    'usuarios': ['ultimo_acceso'],
    'estudiantes': ['ultimo_acceso'],
    'codigos_clase': ['fecha_expiracion'],
}

# server_default=func.now(): en MySQL depende de la zona del servidor (en el VPS
# es -05, ya correcta) pero en SQLite/PostgreSQL sale en UTC.
SERVER_DEFAULT_UTC = {
    'asignaciones_examen': ['fecha_creacion'],
    'codigos_clase': ['fecha_creacion'],
    'docentes': ['fecha_creacion'],
    'estudiantes': ['fecha_creacion'],
    'examenes_lectura': ['fecha_creacion'],
    'examenes_matematica': ['fecha_creacion'],
    'instituciones_educativas': ['fecha_creacion'],
    'intentos_examen': ['fecha_creacion'],
    'matriculas': ['fecha_creacion'],
    'progreso_estudiante': ['fecha_creacion'],
    'ugeles': ['fecha_creacion'],
    'usuarios': ['fecha_creacion'],
}


def _shift_sql(column: str, dialect: str, hours: int) -> str:
    """`hours` es un delta con signo: -5 pasa de UTC a hora Perú, +5 lo revierte."""
    if dialect == 'mysql':
        return f'{column} + INTERVAL {hours} HOUR'
    if dialect == 'postgresql':
        return f"{column} + interval '{hours} hours'"
    return f"datetime({column}, '{hours} hours')"


def _apply(spec: dict, dialect: str, hours: int, inspector) -> None:
    tablas = set(inspector.get_table_names())
    for table, columns in spec.items():
        if table not in tablas:
            continue
        existentes = {c['name'] for c in inspector.get_columns(table)}
        for column in columns:
            if column not in existentes:
                continue
            op.execute(
                f'UPDATE {table} SET {column} = {_shift_sql(column, dialect, hours)} '
                f'WHERE {column} IS NOT NULL'
            )


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa_inspect(bind)

    _apply(PYTHON_UTC, dialect, -5, inspector)
    if dialect != 'mysql':
        _apply(SERVER_DEFAULT_UTC, dialect, -5, inspector)


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa_inspect(bind)

    _apply(PYTHON_UTC, dialect, 5, inspector)
    if dialect != 'mysql':
        _apply(SERVER_DEFAULT_UTC, dialect, 5, inspector)

"""add año_escolar to usuarios, codigos_clase, asignaciones_examen, progreso_estudiante

Revision ID: h1i2j3k4l5m6
Revises: g2h3i4j5k6l7
Create Date: 2026-05-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h1i2j3k4l5m6'
down_revision: Union[str, None] = 'g2h3i4j5k6l7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # IF NOT EXISTS soportado desde MariaDB 10.0 / MySQL 8.0
    op.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS `año_escolar` INTEGER NULL")
    op.execute("ALTER TABLE codigos_clase ADD COLUMN IF NOT EXISTS `año_escolar` INTEGER NOT NULL DEFAULT 2026")
    op.execute("ALTER TABLE asignaciones_examen ADD COLUMN IF NOT EXISTS `año_escolar` INTEGER NULL DEFAULT 2026")
    op.execute("ALTER TABLE progreso_estudiante ADD COLUMN IF NOT EXISTS `año_escolar` INTEGER NULL")

    # Reemplazar unique constraint sin año_escolar por uno que lo incluye
    op.execute("""
        ALTER TABLE progreso_estudiante
            DROP INDEX IF EXISTS uq_progreso_estudiante_area,
            ADD CONSTRAINT uq_progreso_estudiante_area_anio
                UNIQUE (estudiante_id, area, año_escolar)
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE progreso_estudiante
            DROP INDEX IF EXISTS uq_progreso_estudiante_area_anio,
            ADD CONSTRAINT uq_progreso_estudiante_area
                UNIQUE (estudiante_id, area)
    """)
    op.execute("ALTER TABLE progreso_estudiante DROP COLUMN IF EXISTS `año_escolar`")
    op.execute("ALTER TABLE asignaciones_examen DROP COLUMN IF EXISTS `año_escolar`")
    op.execute("ALTER TABLE codigos_clase DROP COLUMN IF EXISTS `año_escolar`")
    op.execute("ALTER TABLE usuarios DROP COLUMN IF EXISTS `año_escolar`")

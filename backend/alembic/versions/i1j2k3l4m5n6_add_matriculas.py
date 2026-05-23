"""add matriculas table, migrate student enrollment data, normalize progreso_estudiante

Revision ID: i1j2k3l4m5n6
Revises: h1i2j3k4l5m6
Create Date: 2026-05-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'i1j2k3l4m5n6'
down_revision: Union[str, None] = 'h1i2j3k4l5m6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Crear tabla matriculas (IF NOT EXISTS — puede existir de ejecución parcial anterior)
    op.execute("""
        CREATE TABLE IF NOT EXISTS matriculas (
            id INT NOT NULL AUTO_INCREMENT,
            estudiante_id INT NOT NULL,
            año_escolar INT NOT NULL,
            grado_id INT NOT NULL,
            seccion VARCHAR(10) NOT NULL,
            institucion_educativa_id INT NOT NULL,
            ugel_id INT NULL,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            fecha_creacion DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            PRIMARY KEY (id),
            UNIQUE KEY uq_matricula_estudiante_anio (estudiante_id, año_escolar),
            KEY ix_matriculas_id (id),
            CONSTRAINT fk_matricula_estudiante FOREIGN KEY (estudiante_id)
                REFERENCES usuarios(id) ON DELETE CASCADE,
            CONSTRAINT fk_matricula_grado FOREIGN KEY (grado_id)
                REFERENCES grados(id),
            CONSTRAINT fk_matricula_ie FOREIGN KEY (institucion_educativa_id)
                REFERENCES instituciones_educativas(id),
            CONSTRAINT fk_matricula_ugel FOREIGN KEY (ugel_id)
                REFERENCES ugeles(id) ON DELETE SET NULL
        )
    """)

    # 2. Migrar datos existentes de usuarios → matriculas
    op.execute("""
        INSERT IGNORE INTO matriculas
            (estudiante_id, año_escolar, grado_id, seccion, institucion_educativa_id, ugel_id, is_active)
        SELECT
            u.id,
            COALESCE(u.año_escolar, 2026),
            u.grado_id,
            u.seccion,
            u.institucion_educativa_id,
            u.ugel_id,
            1
        FROM usuarios u
        INNER JOIN roles r ON u.rol_id = r.id
        WHERE r.codigo = 'estudiante'
          AND u.grado_id IS NOT NULL
          AND u.seccion IS NOT NULL
          AND u.institucion_educativa_id IS NOT NULL
    """)

    # 3. Asegurar estructura correcta en progreso_estudiante
    #    (puede estar ya aplicada por ejecución parcial anterior)
    op.execute("ALTER TABLE progreso_estudiante ADD COLUMN IF NOT EXISTS matricula_id INT NULL")

    # Soltar FK/índices antiguos antes de crear los nuevos
    op.execute("ALTER TABLE progreso_estudiante DROP FOREIGN KEY IF EXISTS progreso_estudiante_ibfk_1")
    op.execute("ALTER TABLE progreso_estudiante DROP FOREIGN KEY IF EXISTS fk_progreso_matricula")
    op.execute("ALTER TABLE progreso_estudiante DROP INDEX IF EXISTS uq_progreso_estudiante_area_anio")

    # Solo intentar crear si no existe (MariaDB no tiene IF NOT EXISTS para constraints)
    op.execute("""
        ALTER TABLE progreso_estudiante
            ADD CONSTRAINT IF NOT EXISTS uq_progreso_matricula_area UNIQUE (matricula_id, area),
            ADD CONSTRAINT IF NOT EXISTS fk_progreso_matricula
                FOREIGN KEY (matricula_id) REFERENCES matriculas(id) ON DELETE CASCADE
    """)

    op.execute("ALTER TABLE progreso_estudiante DROP COLUMN IF EXISTS `año_escolar`")
    op.execute("ALTER TABLE progreso_estudiante DROP COLUMN IF EXISTS `estudiante_id`")

    # 4. Eliminar columnas de inscripción de usuarios (ahora en matriculas)
    op.execute("ALTER TABLE usuarios DROP COLUMN IF EXISTS grado_id")
    op.execute("ALTER TABLE usuarios DROP COLUMN IF EXISTS seccion")
    op.execute("ALTER TABLE usuarios DROP COLUMN IF EXISTS `año_escolar`")


def downgrade() -> None:
    op.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS grado_id INT NULL")
    op.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS seccion VARCHAR(10) NULL")
    op.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS `año_escolar` INT NULL")

    op.execute("""
        UPDATE usuarios u
        INNER JOIN matriculas m ON (m.estudiante_id = u.id AND m.is_active = 1)
        SET u.grado_id = m.grado_id,
            u.seccion = m.seccion,
            u.año_escolar = m.año_escolar
    """)

    op.execute("ALTER TABLE progreso_estudiante ADD COLUMN IF NOT EXISTS estudiante_id INT NULL")
    op.execute("ALTER TABLE progreso_estudiante ADD COLUMN IF NOT EXISTS `año_escolar` INT NULL")
    op.execute("""
        UPDATE progreso_estudiante pe
        INNER JOIN matriculas m ON pe.matricula_id = m.id
        SET pe.estudiante_id = m.estudiante_id,
            pe.año_escolar = m.año_escolar
    """)
    op.execute("ALTER TABLE progreso_estudiante DROP FOREIGN KEY IF EXISTS fk_progreso_matricula")
    op.execute("ALTER TABLE progreso_estudiante DROP INDEX IF EXISTS uq_progreso_matricula_area")
    op.execute("""
        ALTER TABLE progreso_estudiante
            ADD CONSTRAINT uq_progreso_estudiante_area_anio UNIQUE (estudiante_id, area, año_escolar)
    """)
    op.execute("ALTER TABLE progreso_estudiante DROP COLUMN IF EXISTS matricula_id")
    op.execute("DROP TABLE IF EXISTS matriculas")

"""saas_multitenancy_roles_usuarios

Revision ID: b2c4d6e8f0a2
Revises: 6a95e09808be
Create Date: 2026-04-09 00:00:00.000000

Migración Fase 1 + Fase 3:
- Crea: roles, ugeles, instituciones_educativas, codigos_clase
- Renombra docentes → usuarios, agrega columnas nuevas
- Migra is_superuser → rol_id
- Crea: asignaciones_examen, intentos_examen, progreso_estudiante
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect


revision: str = 'b2c4d6e8f0a2'
down_revision: Union[str, None] = '6a95e09808be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, name: str) -> bool:
    result = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name}
    )
    return result.fetchone() is not None


def column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result.fetchall())


def upgrade() -> None:
    conn = op.get_bind()

    # =========================================================================
    # 1. Tabla roles
    # =========================================================================
    if not table_exists(conn, 'roles'):
        conn.execute(text("""
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY,
                codigo VARCHAR(50) NOT NULL UNIQUE,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                nivel INTEGER NOT NULL,
                orden INTEGER NOT NULL
            )
        """))

    # Insertar roles semilla (ignorar si ya existen)
    roles = [
        (1, 'especialista_dre_comunicacion', 'Especialista DRE Comunicación', 'Mantiene desempeños de comunicación a nivel DRE', 1, 1),
        (2, 'especialista_dre_matematica', 'Especialista DRE Matemática', 'Mantiene desempeños de matemática a nivel DRE', 1, 2),
        (3, 'responsable_ugel', 'Responsable UGEL', 'Gestiona su UGEL y sus instituciones educativas', 2, 3),
        (4, 'director', 'Director', 'Director de institución educativa', 3, 4),
        (5, 'auxiliar', 'Auxiliar', 'Auxiliar de institución educativa', 4, 5),
        (6, 'docente', 'Docente', 'Docente que genera y asigna exámenes', 5, 6),
        (7, 'estudiante', 'Estudiante', 'Estudiante que rinde exámenes', 6, 7),
    ]
    for r in roles:
        conn.execute(text(
            "INSERT OR IGNORE INTO roles (id, codigo, nombre, descripcion, nivel, orden) "
            "VALUES (:id, :codigo, :nombre, :descripcion, :nivel, :orden)"
        ), {"id": r[0], "codigo": r[1], "nombre": r[2], "descripcion": r[3], "nivel": r[4], "orden": r[5]})

    # =========================================================================
    # 2. Tabla ugeles
    # =========================================================================
    if not table_exists(conn, 'ugeles'):
        conn.execute(text("""
            CREATE TABLE ugeles (
                id INTEGER PRIMARY KEY,
                codigo VARCHAR(20) NOT NULL UNIQUE,
                nombre VARCHAR(200) NOT NULL,
                provincia_id INTEGER REFERENCES provincias(id) ON DELETE SET NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text(
            "INSERT INTO ugeles (id, codigo, nombre, is_active) VALUES (1, 'SIN-ASIGNAR', 'Sin UGEL asignada', 1)"
        ))

    # =========================================================================
    # 3. Tabla instituciones_educativas
    # =========================================================================
    if not table_exists(conn, 'instituciones_educativas'):
        conn.execute(text("""
            CREATE TABLE instituciones_educativas (
                id INTEGER PRIMARY KEY,
                codigo_modular VARCHAR(20) NOT NULL UNIQUE,
                nombre VARCHAR(300) NOT NULL,
                nivel_educativo VARCHAR(20) NOT NULL,
                direccion TEXT,
                ugel_id INTEGER NOT NULL REFERENCES ugeles(id),
                distrito_id INTEGER REFERENCES distritos(id) ON DELETE SET NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text(
            "INSERT INTO instituciones_educativas (id, codigo_modular, nombre, nivel_educativo, ugel_id, is_active) "
            "VALUES (1, 'SIN-ASIGNAR', 'Sin institución asignada', 'primaria', 1, 1)"
        ))

    # =========================================================================
    # 4. Renombrar docentes → usuarios (si no se ha hecho)
    # =========================================================================
    if table_exists(conn, 'docentes') and not table_exists(conn, 'usuarios'):
        conn.execute(text("ALTER TABLE docentes RENAME TO usuarios"))
    elif not table_exists(conn, 'usuarios'):
        # Crear la tabla usuarios desde cero si no existe ninguna de las dos
        conn.execute(text("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                dni VARCHAR(8) UNIQUE,
                nombres VARCHAR(100),
                apellidos VARCHAR(100),
                profesion VARCHAR(100),
                password_hash VARCHAR(200) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                provincia_id INTEGER REFERENCES provincias(id) ON DELETE SET NULL,
                distrito_id INTEGER REFERENCES distritos(id) ON DELETE SET NULL,
                creado_por_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

    # =========================================================================
    # 5. Agregar columnas nuevas a usuarios
    # =========================================================================
    new_cols = [
        ("codigo_estudiante", "VARCHAR(10)"),
        ("email", "VARCHAR(200)"),
        ("telefono", "VARCHAR(20)"),
        ("rol_id", "INTEGER"),
        ("ugel_id", "INTEGER"),
        ("institucion_educativa_id", "INTEGER"),
        ("grado_id", "INTEGER"),
        ("seccion", "VARCHAR(10)"),
        ("ultimo_acceso", "DATETIME"),
    ]
    for col_name, col_type in new_cols:
        if not column_exists(conn, 'usuarios', col_name):
            conn.execute(text(f"ALTER TABLE usuarios ADD COLUMN {col_name} {col_type}"))

    # =========================================================================
    # 6. Migrar is_superuser → rol_id
    # =========================================================================
    if column_exists(conn, 'usuarios', 'is_superuser'):
        conn.execute(text(
            "UPDATE usuarios SET rol_id = 1 WHERE is_superuser = 1 AND rol_id IS NULL"
        ))
    conn.execute(text(
        "UPDATE usuarios SET rol_id = 6 WHERE rol_id IS NULL"
    ))

    # =========================================================================
    # 7. Tabla codigos_clase
    # =========================================================================
    if not table_exists(conn, 'codigos_clase'):
        conn.execute(text("""
            CREATE TABLE codigos_clase (
                id INTEGER PRIMARY KEY,
                codigo VARCHAR(10) NOT NULL UNIQUE,
                creado_por_id INTEGER NOT NULL REFERENCES usuarios(id),
                institucion_educativa_id INTEGER NOT NULL REFERENCES instituciones_educativas(id),
                grado_id INTEGER NOT NULL REFERENCES grados(id),
                seccion VARCHAR(10) NOT NULL,
                max_estudiantes INTEGER DEFAULT 40,
                is_active BOOLEAN DEFAULT 1,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_expiracion DATETIME
            )
        """))

    # =========================================================================
    # 8. Tabla asignaciones_examen
    # =========================================================================
    if not table_exists(conn, 'asignaciones_examen'):
        conn.execute(text("""
            CREATE TABLE asignaciones_examen (
                id INTEGER PRIMARY KEY,
                tipo_examen VARCHAR(20) NOT NULL,
                examen_lectura_id INTEGER REFERENCES examenes_lectura(id) ON DELETE SET NULL,
                examen_matematica_id INTEGER REFERENCES examenes_matematica(id) ON DELETE SET NULL,
                asignado_por_id INTEGER NOT NULL REFERENCES usuarios(id),
                institucion_educativa_id INTEGER REFERENCES instituciones_educativas(id),
                grado_id INTEGER REFERENCES grados(id),
                seccion VARCHAR(10),
                fecha_inicio DATETIME,
                fecha_fin DATETIME,
                duracion_minutos INTEGER,
                intentos_permitidos INTEGER DEFAULT 1,
                mostrar_resultados BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

    # =========================================================================
    # 9. Tabla intentos_examen
    # =========================================================================
    if not table_exists(conn, 'intentos_examen'):
        conn.execute(text("""
            CREATE TABLE intentos_examen (
                id INTEGER PRIMARY KEY,
                asignacion_id INTEGER NOT NULL REFERENCES asignaciones_examen(id),
                estudiante_id INTEGER NOT NULL REFERENCES usuarios(id),
                numero_intento INTEGER NOT NULL DEFAULT 1,
                estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
                fecha_inicio DATETIME,
                fecha_fin DATETIME,
                respuestas JSON,
                puntaje_total REAL,
                preguntas_correctas INTEGER,
                preguntas_total INTEGER,
                nivel_logro VARCHAR(50),
                resultados_por_desempeno JSON,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(asignacion_id, estudiante_id, numero_intento)
            )
        """))

    # =========================================================================
    # 10. Tabla progreso_estudiante
    # =========================================================================
    if not table_exists(conn, 'progreso_estudiante'):
        conn.execute(text("""
            CREATE TABLE progreso_estudiante (
                id INTEGER PRIMARY KEY,
                estudiante_id INTEGER NOT NULL REFERENCES usuarios(id),
                area VARCHAR(20) NOT NULL,
                total_examenes_completados INTEGER DEFAULT 0,
                puntaje_promedio REAL,
                nivel_logro_actual VARCHAR(50),
                dominio_desempenos JSON,
                ultima_actividad DATETIME,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(estudiante_id, area)
            )
        """))

    # =========================================================================
    # 11. Índices
    # =========================================================================
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_usuarios_codigo_estudiante ON usuarios (codigo_estudiante)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_usuarios_rol_id ON usuarios (rol_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_usuarios_ugel_id ON usuarios (ugel_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_usuarios_ie_id ON usuarios (institucion_educativa_id)"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS progreso_estudiante"))
    conn.execute(text("DROP TABLE IF EXISTS intentos_examen"))
    conn.execute(text("DROP TABLE IF EXISTS asignaciones_examen"))
    conn.execute(text("DROP TABLE IF EXISTS codigos_clase"))

    conn.execute(text("DROP INDEX IF EXISTS ix_usuarios_ie_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_usuarios_ugel_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_usuarios_rol_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_usuarios_codigo_estudiante"))

    # Quitar columnas nuevas (SQLite no tiene DROP COLUMN — requiere recrear tabla)
    # Para simplificar, solo renombramos de vuelta
    if table_exists(conn, 'usuarios') and not table_exists(conn, 'docentes'):
        conn.execute(text("ALTER TABLE usuarios RENAME TO docentes"))

    conn.execute(text("DROP TABLE IF EXISTS instituciones_educativas"))
    conn.execute(text("DROP TABLE IF EXISTS ugeles"))
    conn.execute(text("DROP TABLE IF EXISTS roles"))

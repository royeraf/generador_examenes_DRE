"""Separar tabla estudiantes de usuarios

Revision ID: j2k3l4m5n6o7
Revises: i1j2k3l4m5n6
Create Date: 2026-05-22

Crea tabla `estudiantes` independiente con los campos propios del rol estudiante.
Migra los registros existentes desde `usuarios` preservando los IDs para no romper
las FK en `matriculas` e `intentos_examen`. Luego actualiza las FK constraints
para apuntar a `estudiantes` y elimina los estudiantes de `usuarios`.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'j2k3l4m5n6o7'
down_revision = 'i1j2k3l4m5n6'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))

    # 1. Crear tabla estudiantes
    op.create_table(
        'estudiantes',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('dni', sa.String(8), nullable=True),
        sa.Column('codigo_estudiante', sa.String(10), nullable=True),
        sa.Column('nombres', sa.String(100), nullable=True),
        sa.Column('apellidos', sa.String(100), nullable=True),
        sa.Column('password_hash', sa.String(200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('institucion_educativa_id', sa.Integer(), nullable=True),
        sa.Column('distrito_id', sa.Integer(), nullable=True),
        sa.Column('creado_por_id', sa.Integer(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('ultimo_acceso', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dni', name='uq_estudiante_dni'),
        sa.UniqueConstraint('codigo_estudiante', name='uq_estudiante_codigo'),
        sa.ForeignKeyConstraint(
            ['institucion_educativa_id'], ['instituciones_educativas.id'],
            ondelete='SET NULL', name='fk_estudiante_ie'
        ),
        sa.ForeignKeyConstraint(
            ['distrito_id'], ['distritos.id'],
            ondelete='SET NULL', name='fk_estudiante_distrito'
        ),
        sa.ForeignKeyConstraint(
            ['creado_por_id'], ['usuarios.id'],
            ondelete='SET NULL', name='fk_estudiante_creado_por'
        ),
    )
    op.create_index('ix_estudiantes_id', 'estudiantes', ['id'])
    op.create_index('ix_estudiantes_dni', 'estudiantes', ['dni'])
    op.create_index('ix_estudiantes_codigo', 'estudiantes', ['codigo_estudiante'])

    # 2. Copiar estudiantes desde usuarios (preservando IDs)
    conn.execute(text("""
        INSERT INTO estudiantes
            (id, dni, codigo_estudiante, nombres, apellidos, password_hash, is_active,
             institucion_educativa_id, distrito_id, creado_por_id, fecha_creacion, ultimo_acceso)
        SELECT
            u.id, u.dni, u.codigo_estudiante, u.nombres, u.apellidos,
            u.password_hash, u.is_active,
            u.institucion_educativa_id, u.distrito_id, u.creado_por_id,
            u.fecha_creacion, u.ultimo_acceso
        FROM usuarios u
        JOIN roles r ON u.rol_id = r.id
        WHERE r.codigo = 'estudiante'
    """))

    # 3. Actualizar FK en matriculas: usuarios.id → estudiantes.id
    conn.execute(text("""
        SET @fk_mat = (
            SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'matriculas'
              AND COLUMN_NAME = 'estudiante_id'
              AND REFERENCED_TABLE_NAME = 'usuarios'
            LIMIT 1
        )
    """))
    conn.execute(text("""
        SET @sql_mat = IF(
            @fk_mat IS NOT NULL,
            CONCAT('ALTER TABLE matriculas DROP FOREIGN KEY `', @fk_mat, '`'),
            'SELECT 1'
        )
    """))
    conn.execute(text("PREPARE stmt FROM @sql_mat"))
    conn.execute(text("EXECUTE stmt"))
    conn.execute(text("DEALLOCATE PREPARE stmt"))

    conn.execute(text("""
        ALTER TABLE matriculas
        ADD CONSTRAINT fk_matricula_estudiante
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
    """))

    # 4. Actualizar FK en intentos_examen: usuarios.id → estudiantes.id
    conn.execute(text("""
        SET @fk_int = (
            SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'intentos_examen'
              AND COLUMN_NAME = 'estudiante_id'
              AND REFERENCED_TABLE_NAME = 'usuarios'
            LIMIT 1
        )
    """))
    conn.execute(text("""
        SET @sql_int = IF(
            @fk_int IS NOT NULL,
            CONCAT('ALTER TABLE intentos_examen DROP FOREIGN KEY `', @fk_int, '`'),
            'SELECT 1'
        )
    """))
    conn.execute(text("PREPARE stmt FROM @sql_int"))
    conn.execute(text("EXECUTE stmt"))
    conn.execute(text("DEALLOCATE PREPARE stmt"))

    conn.execute(text("""
        ALTER TABLE intentos_examen
        ADD CONSTRAINT fk_intento_estudiante
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id)
    """))

    # 5. Eliminar estudiantes de usuarios
    conn.execute(text("""
        DELETE u FROM usuarios u
        JOIN roles r ON u.rol_id = r.id
        WHERE r.codigo = 'estudiante'
    """))

    # 6. Eliminar columna codigo_estudiante de usuarios
    op.drop_column('usuarios', 'codigo_estudiante')

    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))

    # Restaurar columna codigo_estudiante en usuarios
    op.add_column('usuarios', sa.Column('codigo_estudiante', sa.String(10), nullable=True))

    # Copiar estudiantes de vuelta a usuarios
    conn.execute(text("""
        INSERT INTO usuarios
            (id, dni, codigo_estudiante, nombres, apellidos, password_hash, is_active,
             institucion_educativa_id, distrito_id, creado_por_id, fecha_creacion, ultimo_acceso, rol_id)
        SELECT
            e.id, e.dni, e.codigo_estudiante, e.nombres, e.apellidos,
            e.password_hash, e.is_active,
            e.institucion_educativa_id, e.distrito_id, e.creado_por_id,
            e.fecha_creacion, e.ultimo_acceso,
            (SELECT id FROM roles WHERE codigo = 'estudiante' LIMIT 1)
        FROM estudiantes e
    """))

    # Restaurar FK en matriculas → usuarios
    conn.execute(text("""
        SET @fk_est = (
            SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'matriculas'
              AND COLUMN_NAME = 'estudiante_id'
              AND REFERENCED_TABLE_NAME = 'estudiantes'
            LIMIT 1
        )
    """))
    conn.execute(text("""
        SET @sql = IF(
            @fk_est IS NOT NULL,
            CONCAT('ALTER TABLE matriculas DROP FOREIGN KEY `', @fk_est, '`'),
            'SELECT 1'
        )
    """))
    conn.execute(text("PREPARE stmt FROM @sql"))
    conn.execute(text("EXECUTE stmt"))
    conn.execute(text("DEALLOCATE PREPARE stmt"))

    conn.execute(text("""
        ALTER TABLE matriculas
        ADD CONSTRAINT fk_matricula_estudiante_orig
        FOREIGN KEY (estudiante_id) REFERENCES usuarios(id) ON DELETE CASCADE
    """))

    # Restaurar FK en intentos_examen → usuarios
    conn.execute(text("""
        SET @fk_int2 = (
            SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'intentos_examen'
              AND COLUMN_NAME = 'estudiante_id'
              AND REFERENCED_TABLE_NAME = 'estudiantes'
            LIMIT 1
        )
    """))
    conn.execute(text("""
        SET @sql2 = IF(
            @fk_int2 IS NOT NULL,
            CONCAT('ALTER TABLE intentos_examen DROP FOREIGN KEY `', @fk_int2, '`'),
            'SELECT 1'
        )
    """))
    conn.execute(text("PREPARE stmt FROM @sql2"))
    conn.execute(text("EXECUTE stmt"))
    conn.execute(text("DEALLOCATE PREPARE stmt"))

    conn.execute(text("""
        ALTER TABLE intentos_examen
        ADD CONSTRAINT fk_intento_estudiante_orig
        FOREIGN KEY (estudiante_id) REFERENCES usuarios(id)
    """))

    # Eliminar tabla estudiantes
    op.drop_table('estudiantes')

    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

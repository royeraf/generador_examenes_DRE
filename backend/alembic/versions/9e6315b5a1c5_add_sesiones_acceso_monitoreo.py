"""add sesiones_acceso monitoreo

Revision ID: 9e6315b5a1c5
Revises: k3l4m5n6o7p8
Create Date: 2026-09-16 16:15:52.559794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e6315b5a1c5'
down_revision: Union[str, None] = 'k3l4m5n6o7p8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sesiones_acceso',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(length=36), nullable=True),
        sa.Column('exito', sa.Boolean(), nullable=False),
        sa.Column('motivo', sa.String(length=50), nullable=True),
        sa.Column('tipo_usuario', sa.String(length=20), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('identificador', sa.String(length=20), nullable=True),
        sa.Column('nombres', sa.String(length=100), nullable=True),
        sa.Column('apellidos', sa.String(length=100), nullable=True),
        sa.Column('rol_codigo', sa.String(length=30), nullable=True),
        sa.Column('institucion_educativa_id', sa.Integer(), nullable=True),
        sa.Column('ugel_id', sa.Integer(), nullable=True),
        sa.Column('ip', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('dispositivo', sa.String(length=20), nullable=True),
        sa.Column('sistema_operativo', sa.String(length=40), nullable=True),
        sa.Column('navegador', sa.String(length=40), nullable=True),
        sa.Column('es_movil', sa.Boolean(), nullable=False),
        sa.Column('login_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('logout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sesiones_acceso_exito'), 'sesiones_acceso', ['exito'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_id'), 'sesiones_acceso', ['id'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_identificador'), 'sesiones_acceso', ['identificador'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_institucion_educativa_id'), 'sesiones_acceso', ['institucion_educativa_id'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_is_active'), 'sesiones_acceso', ['is_active'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_jti'), 'sesiones_acceso', ['jti'], unique=True)
    op.create_index(op.f('ix_sesiones_acceso_last_activity'), 'sesiones_acceso', ['last_activity'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_login_at'), 'sesiones_acceso', ['login_at'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_rol_codigo'), 'sesiones_acceso', ['rol_codigo'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_ugel_id'), 'sesiones_acceso', ['ugel_id'], unique=False)
    op.create_index(op.f('ix_sesiones_acceso_usuario_id'), 'sesiones_acceso', ['usuario_id'], unique=False)
    op.create_index('ix_sesiones_activas', 'sesiones_acceso', ['exito', 'logout_at', 'last_activity'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_sesiones_activas', table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_usuario_id'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_ugel_id'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_rol_codigo'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_login_at'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_last_activity'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_jti'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_is_active'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_institucion_educativa_id'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_identificador'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_id'), table_name='sesiones_acceso')
    op.drop_index(op.f('ix_sesiones_acceso_exito'), table_name='sesiones_acceso')
    op.drop_table('sesiones_acceso')

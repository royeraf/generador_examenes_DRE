"""permisos_modulos por usuario

Revision ID: d4e6f8a0b2c4
Revises: b2c4d6e8f0a2
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e6f8a0b2c4'
down_revision = 'b2c4d6e8f0a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite soporta ADD COLUMN directamente
    op.add_column(
        'usuarios',
        sa.Column('permisos_modulos', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    # SQLite no soporta DROP COLUMN nativo; se deja como no-op
    pass

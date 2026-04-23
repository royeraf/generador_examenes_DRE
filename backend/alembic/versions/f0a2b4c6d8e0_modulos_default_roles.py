"""modulos_default en tabla roles

Revision ID: f0a2b4c6d8e0
Revises: d4e6f8a0b2c4
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'f0a2b4c6d8e0'
down_revision = 'd4e6f8a0b2c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'roles',
        sa.Column('modulos_default', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    pass

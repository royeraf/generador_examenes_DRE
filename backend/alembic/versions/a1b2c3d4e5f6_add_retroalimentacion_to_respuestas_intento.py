"""add retroalimentacion_ia to respuestas_intento

Revision ID: a1b2c3d4e5f6
Revises: c1d2e3f4a5b6
Create Date: 2026-05-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('respuestas_intento') as batch_op:
        batch_op.add_column(sa.Column('retroalimentacion_ia', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('respuestas_intento') as batch_op:
        batch_op.drop_column('retroalimentacion_ia')

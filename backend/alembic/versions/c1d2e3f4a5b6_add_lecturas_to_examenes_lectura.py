"""add lecturas json to examenes_lectura

Revision ID: c1d2e3f4a5b6
Revises: e8f1c2d3a4b5
Create Date: 2026-05-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'e8f1c2d3a4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('examenes_lectura') as batch_op:
        batch_op.add_column(sa.Column('lecturas', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('examenes_lectura') as batch_op:
        batch_op.drop_column('lecturas')

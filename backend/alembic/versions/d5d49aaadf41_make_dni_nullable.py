"""make_dni_nullable

Revision ID: d5d49aaadf41
Revises: a2c4e6f8b0d2
Create Date: 2026-04-30 10:00:01.400927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5d49aaadf41'
down_revision: Union[str, None] = 'a2c4e6f8b0d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.alter_column('dni',
                              existing_type=sa.VARCHAR(length=8),
                              nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.alter_column('dni',
                              existing_type=sa.VARCHAR(length=8),
                              nullable=False)

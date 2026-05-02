"""add shuffle options to asignaciones

Revision ID: e8f1c2d3a4b5
Revises: 145a50c01758
Create Date: 2026-05-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8f1c2d3a4b5'
down_revision: Union[str, None] = '145a50c01758'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.add_column(sa.Column('mezclar_preguntas', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('mezclar_alternativas', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.drop_column('mezclar_alternativas')
        batch_op.drop_column('mezclar_preguntas')

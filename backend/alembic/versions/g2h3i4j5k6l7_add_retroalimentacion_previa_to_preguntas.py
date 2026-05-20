"""add retroalimentacion_correcta e incorrecta to preguntas_examen

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-05-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g2h3i4j5k6l7'
down_revision: Union[str, None] = 'a1b2c3e4f5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('preguntas_examen') as batch_op:
        batch_op.add_column(sa.Column('retroalimentacion_correcta', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('retroalimentacion_incorrecta', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('preguntas_examen') as batch_op:
        batch_op.drop_column('retroalimentacion_incorrecta')
        batch_op.drop_column('retroalimentacion_correcta')

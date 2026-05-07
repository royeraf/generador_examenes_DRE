"""drop unused JSON columns from intentos_examen

Revision ID: a3b5c7d9e1f3
Revises: a1b2c3d4e5f6
Create Date: 2026-05-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a3b5c7d9e1f3'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('intentos_examen') as batch_op:
        batch_op.drop_column('respuestas')
        batch_op.drop_column('resultados_por_desempeno')


def downgrade() -> None:
    with op.batch_alter_table('intentos_examen') as batch_op:
        batch_op.add_column(sa.Column('resultados_por_desempeno', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('respuestas', sa.JSON(), nullable=True))

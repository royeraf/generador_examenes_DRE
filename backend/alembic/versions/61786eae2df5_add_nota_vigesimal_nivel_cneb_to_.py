"""add_nota_vigesimal_nivel_cneb_to_intentos

Revision ID: 61786eae2df5
Revises: d7e8f9a0b1c2
Create Date: 2026-10-20 12:00:36.259213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61786eae2df5'
down_revision: Union[str, None] = 'd7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('intentos_examen', sa.Column('nota_vigesimal', sa.Float(), nullable=True))
    op.add_column('intentos_examen', sa.Column('nivel_cneb', sa.String(length=2), nullable=True))


def downgrade() -> None:
    op.drop_column('intentos_examen', 'nivel_cneb')
    op.drop_column('intentos_examen', 'nota_vigesimal')

"""expand nivel and desempeno_codigo columns in preguntas_examen

Revision ID: f1a2b3c4d5e6
Revises: c5d7e9f1a3b5
Create Date: 2026-05-16

AI returns nivel as full descriptive text (40+ chars) but column was VARCHAR(20).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'c5d7e9f1a3b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('preguntas_examen') as batch_op:
        batch_op.alter_column('nivel',
                              existing_type=sa.String(20),
                              type_=sa.String(100),
                              existing_nullable=True)
        batch_op.alter_column('desempeno_codigo',
                              existing_type=sa.String(50),
                              type_=sa.String(100),
                              existing_nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('preguntas_examen') as batch_op:
        batch_op.alter_column('nivel',
                              existing_type=sa.String(100),
                              type_=sa.String(20),
                              existing_nullable=True)
        batch_op.alter_column('desempeno_codigo',
                              existing_type=sa.String(100),
                              type_=sa.String(50),
                              existing_nullable=True)

"""add check constraints to preguntas_examen and asignaciones_examen

Revision ID: c5d7e9f1a3b5
Revises: b4c6d8e0f2a4
Create Date: 2026-05-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c5d7e9f1a3b5'
down_revision: Union[str, None] = 'b4c6d8e0f2a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('preguntas_examen') as batch_op:
        batch_op.create_check_constraint(
            'ck_pregunta_exactamente_un_examen',
            "(examen_lectura_id IS NOT NULL AND examen_matematica_id IS NULL) OR "
            "(examen_lectura_id IS NULL AND examen_matematica_id IS NOT NULL)",
        )

    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.create_check_constraint(
            'ck_asignacion_tipo_examen',
            "tipo_examen IN ('lectura', 'matematica')",
        )


def downgrade() -> None:
    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.drop_constraint('ck_asignacion_tipo_examen', type_='check')

    with op.batch_alter_table('preguntas_examen') as batch_op:
        batch_op.drop_constraint('ck_pregunta_exactamente_un_examen', type_='check')

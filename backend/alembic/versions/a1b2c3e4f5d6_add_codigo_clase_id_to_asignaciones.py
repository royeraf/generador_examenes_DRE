"""add codigo_clase_id to asignaciones_examen

Revision ID: a1b2c3e4f5d6
Revises: f1a2b3c4d5e6
Create Date: 2026-05-16

Normalización: enlaza cada asignación con el código de clase que la originó.
grado_id + seccion se siguen llenando (derivados del código) para mantener
compatibilidad con la lógica de filtrado de estudiantes.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3e4f5d6'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.add_column(sa.Column('codigo_clase_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_asignacion_codigo_clase',
            'codigos_clase', ['codigo_clase_id'], ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.drop_constraint('fk_asignacion_codigo_clase', type_='foreignkey')
        batch_op.drop_column('codigo_clase_id')

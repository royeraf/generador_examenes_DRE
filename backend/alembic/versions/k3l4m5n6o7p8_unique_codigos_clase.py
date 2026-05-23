"""unique constraint codigos_clase por ie grado seccion año

Revision ID: k3l4m5n6o7p8
Revises: j2k3l4m5n6o7
Create Date: 2026-05-23
"""
from alembic import op

revision = 'k3l4m5n6o7p8'
down_revision = 'j2k3l4m5n6o7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        'uq_aula_ie_grado_seccion_anio',
        'codigos_clase',
        ['institucion_educativa_id', 'grado_id', 'seccion', 'año_escolar'],
    )


def downgrade():
    op.drop_constraint('uq_aula_ie_grado_seccion_anio', 'codigos_clase', type_='unique')

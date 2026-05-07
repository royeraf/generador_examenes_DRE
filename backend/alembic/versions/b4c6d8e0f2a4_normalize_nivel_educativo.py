"""normalize nivel_educativo to junction table institucion_niveles

Revision ID: b4c6d8e0f2a4
Revises: a3b5c7d9e1f3
Create Date: 2026-05-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import json

revision: str = 'b4c6d8e0f2a4'
down_revision: Union[str, None] = 'a3b5c7d9e1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'institucion_niveles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('institucion_id', sa.Integer(), sa.ForeignKey('instituciones_educativas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nivel', sa.String(20), nullable=False),
        sa.UniqueConstraint('institucion_id', 'nivel', name='uq_institucion_nivel'),
    )

    conn = op.get_bind()
    rows = conn.execute(text("SELECT id, nivel_educativo FROM instituciones_educativas")).fetchall()
    for row in rows:
        try:
            niveles = json.loads(row[1]) if row[1] else []
        except (TypeError, ValueError):
            niveles = [row[1]] if row[1] else []
        for nivel in niveles:
            conn.execute(
                text("INSERT INTO institucion_niveles (institucion_id, nivel) VALUES (:iid, :nivel)"),
                {"iid": row[0], "nivel": nivel},
            )

    with op.batch_alter_table('instituciones_educativas') as batch_op:
        batch_op.drop_column('nivel_educativo')


def downgrade() -> None:
    with op.batch_alter_table('instituciones_educativas') as batch_op:
        batch_op.add_column(sa.Column('nivel_educativo', sa.JSON(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(text("SELECT institucion_id, nivel FROM institucion_niveles ORDER BY institucion_id")).fetchall()
    grouped: dict = {}
    for row in rows:
        grouped.setdefault(row[0], []).append(row[1])
    for iid, niveles in grouped.items():
        conn.execute(
            text("UPDATE instituciones_educativas SET nivel_educativo = :val WHERE id = :iid"),
            {"val": json.dumps(niveles), "iid": iid},
        )

    op.drop_table('institucion_niveles')

"""normalize nivel_educativo to junction table institucion_niveles

Revision ID: b4c6d8e0f2a4
Revises: a3b5c7d9e1f3
Create Date: 2026-05-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect as sa_inspect
import json

revision: str = 'b4c6d8e0f2a4'
down_revision: Union[str, None] = 'a3b5c7d9e1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)

    # Crear institucion_niveles si no existe
    if not inspector.has_table('institucion_niveles'):
        op.create_table(
            'institucion_niveles',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('institucion_id', sa.Integer(), sa.ForeignKey('instituciones_educativas.id', ondelete='CASCADE'), nullable=False),
            sa.Column('nivel', sa.String(20), nullable=False),
            sa.UniqueConstraint('institucion_id', 'nivel', name='uq_institucion_nivel'),
        )

    # Migrar datos solo si nivel_educativo todavía existe como columna
    if inspector.has_table('instituciones_educativas'):
        cols = {c['name'] for c in inspector.get_columns('instituciones_educativas')}
        if 'nivel_educativo' in cols:
            rows = conn.execute(text("SELECT id, nivel_educativo FROM instituciones_educativas")).fetchall()
            for row in rows:
                try:
                    niveles = json.loads(row[1]) if row[1] else []
                except (TypeError, ValueError):
                    niveles = [row[1]] if row[1] else []
                for nivel in niveles:
                    conn.execute(
                        text("INSERT IGNORE INTO institucion_niveles (institucion_id, nivel) VALUES (:iid, :nivel)"),
                        {"iid": row[0], "nivel": nivel},
                    )
            with op.batch_alter_table('instituciones_educativas') as batch_op:
                batch_op.drop_column('nivel_educativo')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    cols = {c['name'] for c in inspector.get_columns('instituciones_educativas')} if inspector.has_table('instituciones_educativas') else set()
    if 'nivel_educativo' not in cols:
        with op.batch_alter_table('instituciones_educativas') as batch_op:
            batch_op.add_column(sa.Column('nivel_educativo', sa.JSON(), nullable=True))

    if inspector.has_table('institucion_niveles'):
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

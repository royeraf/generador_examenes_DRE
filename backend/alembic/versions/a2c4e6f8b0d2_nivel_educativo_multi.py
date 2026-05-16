"""nivel_educativo como lista (multi-nivel por institución)

Revision ID: a2c4e6f8b0d2
Revises: f0a2b4c6d8e0
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect as sa_inspect

revision = 'a2c4e6f8b0d2'
down_revision = 'f0a2b4c6d8e0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    # La columna nivel_educativo fue normalizada a institucion_niveles en builds nuevos.
    # Solo ejecutar si todavía existe como columna plana.
    if not inspector.has_table('instituciones_educativas'):
        return
    cols = {c['name'] for c in inspector.get_columns('instituciones_educativas')}
    if 'nivel_educativo' not in cols:
        return
    json_array_fn = "json_array" if conn.dialect.name == "sqlite" else "JSON_ARRAY"
    conn.execute(text(
        f"UPDATE instituciones_educativas "
        f"SET nivel_educativo = {json_array_fn}(nivel_educativo) "
        f"WHERE nivel_educativo NOT LIKE '[%'"
    ))


def downgrade() -> None:
    # No-op: no podemos revertir fácilmente sin pérdida de datos
    pass

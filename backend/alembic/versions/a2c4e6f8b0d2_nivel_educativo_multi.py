"""nivel_educativo como lista (multi-nivel por institución)

Revision ID: a2c4e6f8b0d2
Revises: f0a2b4c6d8e0
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'a2c4e6f8b0d2'
down_revision = 'f0a2b4c6d8e0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convertir valores string a JSON array en SQLite
    conn = op.get_bind()
    conn.execute(text(
        "UPDATE instituciones_educativas "
        "SET nivel_educativo = json_array(nivel_educativo) "
        "WHERE nivel_educativo NOT LIKE '[%'"
    ))


def downgrade() -> None:
    # No-op: no podemos revertir fácilmente sin pérdida de datos
    pass

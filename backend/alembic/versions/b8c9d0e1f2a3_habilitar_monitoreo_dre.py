"""habilitar modulo monitoreo a usuarios DRE existentes

Revision ID: b8c9d0e1f2a3
Revises: 9e6315b5a1c5
Create Date: 2026-09-16 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = '9e6315b5a1c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DRE_ROLES = ('especialista_dre_comunicacion', 'especialista_dre_matematica')
MODULO = 'monitoreo'


def _roles():
    return sa.table(
        'roles',
        sa.column('id', sa.Integer),
        sa.column('codigo', sa.String),
    )


def _usuarios():
    return sa.table(
        'usuarios',
        sa.column('id', sa.Integer),
        sa.column('rol_id', sa.Integer),
        sa.column('permisos_modulos', sa.JSON),
    )


def _dre_role_ids(conn) -> list:
    roles = _roles()
    rows = conn.execute(
        sa.select(roles.c.id).where(roles.c.codigo.in_(DRE_ROLES))
    ).fetchall()
    return [r[0] for r in rows]


def upgrade() -> None:
    conn = op.get_bind()
    usuarios = _usuarios()
    dre_ids = _dre_role_ids(conn)
    if not dre_ids:
        return

    rows = conn.execute(
        sa.select(usuarios.c.id, usuarios.c.permisos_modulos).where(
            usuarios.c.rol_id.in_(dre_ids)
        )
    ).fetchall()

    for usuario_id, permisos in rows:
        if permisos and MODULO not in permisos:
            conn.execute(
                sa.update(usuarios)
                .where(usuarios.c.id == usuario_id)
                .values(permisos_modulos=[*permisos, MODULO])
            )


def downgrade() -> None:
    conn = op.get_bind()
    usuarios = _usuarios()
    dre_ids = _dre_role_ids(conn)
    if not dre_ids:
        return

    rows = conn.execute(
        sa.select(usuarios.c.id, usuarios.c.permisos_modulos).where(
            usuarios.c.rol_id.in_(dre_ids)
        )
    ).fetchall()

    for usuario_id, permisos in rows:
        if permisos and MODULO in permisos:
            conn.execute(
                sa.update(usuarios)
                .where(usuarios.c.id == usuario_id)
                .values(permisos_modulos=[m for m in permisos if m != MODULO])
            )

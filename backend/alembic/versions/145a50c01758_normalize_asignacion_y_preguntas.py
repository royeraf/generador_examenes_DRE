"""normalize_asignacion_y_preguntas

Revision ID: 145a50c01758
Revises: d5d49aaadf41
Create Date: 2026-04-30

Cambios:
1. asignaciones_examen: reemplaza examen_lectura_id + examen_matematica_id por examen_id
2. Crea tabla preguntas_examen
3. Crea tabla respuestas_intento
4. Migra datos existentes de examenes hacia preguntas_examen
"""
import json
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '145a50c01758'
down_revision: Union[str, None] = 'd5d49aaadf41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. asignaciones_examen: examen_id reemplaza a las dos FK nullable ────────
    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.add_column(sa.Column('examen_id', sa.Integer(), nullable=True))

    conn.execute(sa.text(
        "UPDATE asignaciones_examen SET examen_id = COALESCE(examen_lectura_id, examen_matematica_id)"
    ))

    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.alter_column('examen_id', nullable=False)
        batch_op.drop_column('examen_lectura_id')
        batch_op.drop_column('examen_matematica_id')

    # ── 2. Crear preguntas_examen ─────────────────────────────────────────────────
    op.create_table(
        'preguntas_examen',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('examen_lectura_id', sa.Integer(),
                  sa.ForeignKey('examenes_lectura.id', ondelete='CASCADE'), nullable=True),
        sa.Column('examen_matematica_id', sa.Integer(),
                  sa.ForeignKey('examenes_matematica.id', ondelete='CASCADE'), nullable=True),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('enunciado', sa.Text(), nullable=False),
        sa.Column('opcion_a', sa.Text(), nullable=False),
        sa.Column('opcion_b', sa.Text(), nullable=False),
        sa.Column('opcion_c', sa.Text(), nullable=False),
        sa.Column('opcion_d', sa.Text(), nullable=False),
        sa.Column('respuesta_correcta', sa.String(1), nullable=False),
        sa.Column('nivel', sa.String(20), nullable=True),
        sa.Column('desempeno_codigo', sa.String(50), nullable=True),
        sa.Column('desempeno_descripcion', sa.Text(), nullable=True),
        sa.Column('justificacion', sa.Text(), nullable=True),
    )

    # ── 3. Crear respuestas_intento ───────────────────────────────────────────────
    op.create_table(
        'respuestas_intento',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('intento_id', sa.Integer(),
                  sa.ForeignKey('intentos_examen.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pregunta_id', sa.Integer(),
                  sa.ForeignKey('preguntas_examen.id', ondelete='CASCADE'), nullable=False),
        sa.Column('respuesta_dada', sa.String(1), nullable=False),
        sa.Column('es_correcta', sa.Boolean(), nullable=False),
        sa.UniqueConstraint('intento_id', 'pregunta_id', name='uq_respuesta_intento'),
    )

    # ── 4. Migrar preguntas existentes desde JSON ─────────────────────────────────
    def _parse(raw):
        if raw is None:
            return []
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return []
        return raw if isinstance(raw, list) else []

    def _migrar(rows, col_examen):
        for row in rows:
            examen_id, preguntas_raw, tabla_raw = row[0], row[1], row[2]
            preguntas = _parse(preguntas_raw)
            tabla = _parse(tabla_raw)
            tabla_map = {r.get("pregunta"): r for r in tabla}
            for p in preguntas:
                num = p.get("numero", 0)
                opciones = {o["letra"]: o["texto"] for o in p.get("opciones", [])}
                info = tabla_map.get(num, {})
                conn.execute(sa.text(f"""
                    INSERT INTO preguntas_examen
                        ({col_examen}, numero, enunciado,
                         opcion_a, opcion_b, opcion_c, opcion_d,
                         respuesta_correcta, nivel, desempeno_codigo,
                         desempeno_descripcion, justificacion)
                    VALUES
                        (:eid, :num, :enunciado,
                         :a, :b, :c, :d,
                         :rc, :nivel, :dc, :dd, :just)
                """), {
                    "eid": examen_id, "num": num,
                    "enunciado": p.get("enunciado", ""),
                    "a": opciones.get("A", ""), "b": opciones.get("B", ""),
                    "c": opciones.get("C", ""), "d": opciones.get("D", ""),
                    "rc": info.get("respuesta_correcta", ""),
                    "nivel": p.get("nivel") or info.get("nivel"),
                    "dc": p.get("desempeno_codigo") or info.get("desempeno"),
                    "dd": info.get("desempeno"),
                    "just": info.get("justificacion"),
                })

    rows_lec = conn.execute(
        sa.text("SELECT id, preguntas, tabla_respuestas FROM examenes_lectura")
    ).fetchall()
    _migrar(rows_lec, "examen_lectura_id")

    rows_mat = conn.execute(
        sa.text("SELECT id, preguntas, tabla_respuestas FROM examenes_matematica")
    ).fetchall()
    _migrar(rows_mat, "examen_matematica_id")


def downgrade() -> None:
    op.drop_table('respuestas_intento')
    op.drop_table('preguntas_examen')

    with op.batch_alter_table('asignaciones_examen') as batch_op:
        batch_op.add_column(sa.Column('examen_lectura_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('examen_matematica_id', sa.Integer(), nullable=True))
        batch_op.drop_column('examen_id')

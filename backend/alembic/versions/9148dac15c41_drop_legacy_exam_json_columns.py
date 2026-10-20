"""drop legacy exam json columns

Revision ID: 9148dac15c41
Revises: 9491561512f1
Create Date: 2026-10-20 15:05:49.632483

Release B de la normalización:

- Elimina las columnas JSON legacy de ``examenes_lectura`` y
  ``examenes_matematica``. La fuente de verdad son ``textos_examen`` y
  ``preguntas_examen``.
- Antes de borrar, verifica que todo el contenido legacy tenga su equivalente
  normalizado. Si falta algo, la migración aborta sin borrar nada.
- El downgrade vuelve a crear las columnas y las rellena desde las tablas
  normalizadas.
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9148dac15c41'
down_revision: Union[str, None] = '9491561512f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _texto_concatenado(lecturas: list[dict]) -> str:
    if not lecturas:
        return ""
    if len(lecturas) == 1:
        return lecturas[0].get("texto") or ""
    partes = []
    for indice, item in enumerate(lecturas, start=1):
        titulo = (item.get("titulo") or "").strip()
        header = f"TEXTO {indice}: {titulo}" if titulo else f"TEXTO {indice}"
        partes.append(
            f"{'─' * 40}\n{header}\n{'─' * 40}\n{item.get('texto') or ''}"
        )
    return "\n\n".join(partes)


def _verificar_backfill(conn) -> None:
    """Aborta si queda contenido legacy que no esté en las tablas normalizadas."""
    checks = (
        (
            "textos de lectura",
            """
            SELECT id FROM examenes_lectura e
            WHERE (
                (e.lectura IS NOT NULL AND TRIM(e.lectura) <> '')
                OR (
                    e.lecturas IS NOT NULL
                    AND TRIM(CAST(e.lecturas AS CHAR)) NOT IN ('', 'null', '[]')
                )
            )
            AND NOT EXISTS (
                SELECT 1 FROM textos_examen t WHERE t.examen_lectura_id = e.id
            )
            LIMIT 10
            """,
        ),
        (
            "textos de matemática",
            """
            SELECT id FROM examenes_matematica e
            WHERE (
                e.situacion_problematica IS NOT NULL
                AND TRIM(e.situacion_problematica) <> ''
            )
            AND NOT EXISTS (
                SELECT 1 FROM textos_examen t WHERE t.examen_matematica_id = e.id
            )
            LIMIT 10
            """,
        ),
        (
            "preguntas de lectura",
            """
            SELECT id FROM examenes_lectura e
            WHERE (
                e.preguntas IS NOT NULL
                AND TRIM(CAST(e.preguntas AS CHAR)) NOT IN ('', 'null', '[]')
            )
            AND NOT EXISTS (
                SELECT 1 FROM preguntas_examen p WHERE p.examen_lectura_id = e.id
            )
            LIMIT 10
            """,
        ),
        (
            "preguntas de matemática",
            """
            SELECT id FROM examenes_matematica e
            WHERE (
                e.preguntas IS NOT NULL
                AND TRIM(CAST(e.preguntas AS CHAR)) NOT IN ('', 'null', '[]')
            )
            AND NOT EXISTS (
                SELECT 1 FROM preguntas_examen p WHERE p.examen_matematica_id = e.id
            )
            LIMIT 10
            """,
        ),
        (
            "tabla de respuestas de lectura",
            """
            SELECT id FROM examenes_lectura e
            WHERE (
                e.tabla_respuestas IS NOT NULL
                AND TRIM(CAST(e.tabla_respuestas AS CHAR)) NOT IN ('', 'null', '[]')
            )
            AND NOT EXISTS (
                SELECT 1 FROM preguntas_examen p WHERE p.examen_lectura_id = e.id
            )
            LIMIT 10
            """,
        ),
        (
            "tabla de respuestas de matemática",
            """
            SELECT id FROM examenes_matematica e
            WHERE (
                e.tabla_respuestas IS NOT NULL
                AND TRIM(CAST(e.tabla_respuestas AS CHAR)) NOT IN ('', 'null', '[]')
            )
            AND NOT EXISTS (
                SELECT 1 FROM preguntas_examen p WHERE p.examen_matematica_id = e.id
            )
            LIMIT 10
            """,
        ),
    )

    problemas = []
    for nombre, sql in checks:
        ids = [fila[0] for fila in conn.execute(sa.text(sql)).fetchall()]
        if ids:
            problemas.append(f"{nombre}: exámenes {ids}")

    if problemas:
        raise RuntimeError(
            "Release B abortada: hay contenido legacy sin normalizar. "
            "Ejecuta primero el backfill de 9491561512f1 o revisa estos casos: "
            + "; ".join(problemas)
        )


def upgrade() -> None:
    conn = op.get_bind()
    _verificar_backfill(conn)

    with op.batch_alter_table("examenes_lectura") as batch_op:
        batch_op.drop_column("tabla_respuestas")
        batch_op.drop_column("preguntas")
        batch_op.drop_column("lecturas")
        batch_op.drop_column("lectura")

    with op.batch_alter_table("examenes_matematica") as batch_op:
        batch_op.drop_column("tabla_respuestas")
        batch_op.drop_column("preguntas")
        batch_op.drop_column("situacion_problematica")


def downgrade() -> None:
    conn = op.get_bind()

    with op.batch_alter_table("examenes_lectura") as batch_op:
        batch_op.add_column(sa.Column("lectura", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("lecturas", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("preguntas", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("tabla_respuestas", sa.JSON(), nullable=True))

    with op.batch_alter_table("examenes_matematica") as batch_op:
        batch_op.add_column(sa.Column("situacion_problematica", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("preguntas", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("tabla_respuestas", sa.JSON(), nullable=True))

    def _preguntas_legacy(examen_id: int, columna: str) -> tuple[list[dict], list[dict]]:
        filas = conn.execute(sa.text(f"""
            SELECT numero, tipo, enunciado, contexto, opcion_a, opcion_b, opcion_c,
                   opcion_d, opcion_e, respuesta_correcta, respuesta_esperada,
                   espacio_respuesta, nivel, desempeno_codigo, desempeno_descripcion,
                   criterio_evaluacion, justificacion,
                   retroalimentacion_correcta, retroalimentacion_incorrecta
            FROM preguntas_examen
            WHERE {columna} = :eid
            ORDER BY numero
        """), {"eid": examen_id}).fetchall()

        preguntas = []
        tabla = []
        for f in filas:
            opciones = []
            for letra, texto in (
                ("A", f[4]), ("B", f[5]), ("C", f[6]), ("D", f[7]), ("E", f[8])
            ):
                if texto is not None and str(texto).strip() != "":
                    opciones.append({
                        "letra": letra,
                        "texto": texto,
                        "es_correcta": (f[9] or "").upper() == letra,
                    })
            preguntas.append({
                "numero": f[0],
                "enunciado": f[2],
                "opciones": opciones,
                "desempeno_codigo": f[13] or "",
                "nivel": f[12] or "",
                "tipo": f[1] or "cerrada",
                "contexto": f[3],
            })
            tabla.append({
                "pregunta": f[0],
                "desempeno": f[14] or "",
                "nivel": f[12] or "",
                "respuesta_correcta": f[9] or "",
                "respuesta_esperada": f[10],
                "justificacion": f[16] or "",
                "retroalimentacion_correcta": f[17] or "",
                "retroalimentacion_incorrecta": f[18] or "",
            })
        return preguntas, tabla

    for (examen_id,) in conn.execute(sa.text("SELECT id FROM examenes_lectura")).fetchall():
        textos = conn.execute(sa.text("""
            SELECT orden, titulo, texto FROM textos_examen
            WHERE examen_lectura_id = :eid ORDER BY orden
        """), {"eid": examen_id}).fetchall()
        lecturas = [{"titulo": t[1] or "", "texto": t[2] or ""} for t in textos]
        preguntas, tabla = _preguntas_legacy(examen_id, "examen_lectura_id")
        conn.execute(sa.text("""
            UPDATE examenes_lectura
            SET lectura = :lectura, lecturas = :lecturas,
                preguntas = :preguntas, tabla_respuestas = :tabla
            WHERE id = :eid
        """), {
            "lectura": _texto_concatenado(lecturas) if lecturas else None,
            "lecturas": _dump(lecturas) if lecturas else None,
            "preguntas": _dump(preguntas),
            "tabla": _dump(tabla),
            "eid": examen_id,
        })

    for (examen_id,) in conn.execute(sa.text("SELECT id FROM examenes_matematica")).fetchall():
        textos = conn.execute(sa.text("""
            SELECT texto FROM textos_examen
            WHERE examen_matematica_id = :eid ORDER BY orden
        """), {"eid": examen_id}).fetchall()
        situacion = "\n\n".join(t[0] or "" for t in textos) if textos else None
        preguntas, tabla = _preguntas_legacy(examen_id, "examen_matematica_id")
        conn.execute(sa.text("""
            UPDATE examenes_matematica
            SET situacion_problematica = :situacion,
                preguntas = :preguntas, tabla_respuestas = :tabla
            WHERE id = :eid
        """), {
            "situacion": situacion,
            "preguntas": _dump(preguntas),
            "tabla": _dump(tabla),
            "eid": examen_id,
        })

"""normalize_exam_texts_questions

Revision ID: 9491561512f1
Revises: 61786eae2df5
Create Date: 2026-10-20

Normaliza los textos y preguntas generados:

1. Crea ``textos_examen`` (1..N textos por examen) y migra
   ``examenes_lectura.lecturas``/``lectura`` y
   ``examenes_matematica.situacion_problematica``.
2. Amplía ``preguntas_examen`` con ``tipo``, ``contexto``, ``respuesta_esperada``,
   ``espacio_respuesta``, ``criterio_evaluacion`` y ``opcion_e``.
3. Enriquece las preguntas normalizadas desde los JSON ``preguntas`` y
   ``tabla_respuestas`` (incluye la 5.ª alternativa de MatSistem).
4. Agrega restricciones de unicidad y permite respuestas abiertas.

Las columnas JSON/texto anteriores se conservan en esta release para permitir
rollback; su eliminación se hará en una migración posterior.
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9491561512f1'
down_revision: Union[str, None] = '61786eae2df5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# =============================================================================
# Helpers
# =============================================================================

def _parse(raw):
    """Convierte el valor de una columna JSON (str/bytes/objeto) a lista/dict."""
    if raw is None:
        return []
    if isinstance(raw, (list, dict)):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="ignore")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return []
    return []


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _texto_concatenado(items: list[dict]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0].get("texto") or ""
    partes = []
    for indice, item in enumerate(items, start=1):
        titulo = (item.get("titulo") or "").strip()
        header = f"TEXTO {indice}: {titulo}" if titulo else f"TEXTO {indice}"
        partes.append(f"{'─' * 40}\n{header}\n{'─' * 40}\n{item.get('texto') or ''}")
    return "\n\n".join(partes)


def _tabla_desde_preguntas(preguntas: list[dict], tabla: list[dict]) -> list[dict]:
    """Reconstruye ``tabla_respuestas`` desde las preguntas normalizadas."""
    filas = []
    for p in preguntas:
        if not isinstance(p, dict):
            continue
        filas.append({
            "pregunta": p.get("numero"),
            "desempeno": p.get("desempeno") or "",
            "nivel": p.get("nivel") or "",
            "respuesta_correcta": p.get("respuesta_correcta") or "",
            "respuesta_esperada": p.get("respuesta_esperada"),
            "justificacion": p.get("justificacion") or "",
            "retroalimentacion_correcta": p.get("retroalimentacion_correcta") or "",
            "retroalimentacion_incorrecta": p.get("retroalimentacion_incorrecta") or "",
        })
    return filas


def _indices(conn, tabla: str) -> set[str]:
    try:
        return {ix["name"] for ix in sa.inspect(conn).get_indexes(tabla)}
    except Exception:
        return set()


# =============================================================================
# Upgrade
# =============================================================================

def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. textos_examen ─────────────────────────────────────────────────
    op.create_table(
        "textos_examen",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "examen_lectura_id", sa.Integer(),
            sa.ForeignKey("examenes_lectura.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column(
            "examen_matematica_id", sa.Integer(),
            sa.ForeignKey("examenes_matematica.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=True),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "(examen_lectura_id IS NOT NULL AND examen_matematica_id IS NULL) OR "
            "(examen_lectura_id IS NULL AND examen_matematica_id IS NOT NULL)",
            name="ck_texto_exactamente_un_examen",
        ),
        sa.UniqueConstraint("examen_lectura_id", "orden", name="uq_texto_lectura_orden"),
        sa.UniqueConstraint("examen_matematica_id", "orden", name="uq_texto_matematica_orden"),
    )
    op.create_index("ix_textos_examen_id", "textos_examen", ["id"])
    op.create_index("ix_textos_examen_examen_lectura_id", "textos_examen", ["examen_lectura_id"])
    op.create_index("ix_textos_examen_examen_matematica_id", "textos_examen", ["examen_matematica_id"])

    # ── 2. Ampliar preguntas_examen ──────────────────────────────────────
    with op.batch_alter_table("preguntas_examen") as batch_op:
        batch_op.add_column(sa.Column(
            "tipo", sa.String(20), nullable=False, server_default="cerrada",
        ))
        batch_op.add_column(sa.Column("contexto", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("respuesta_esperada", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("espacio_respuesta", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("opcion_e", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("criterio_evaluacion", sa.Text(), nullable=True))
        batch_op.alter_column("opcion_a", existing_type=sa.Text(), nullable=True)
        batch_op.alter_column("opcion_b", existing_type=sa.Text(), nullable=True)
        batch_op.alter_column("opcion_c", existing_type=sa.Text(), nullable=True)
        batch_op.alter_column("opcion_d", existing_type=sa.Text(), nullable=True)
        batch_op.alter_column("respuesta_correcta", existing_type=sa.String(1), nullable=True)

    # ── 3. Respuestas abiertas ───────────────────────────────────────────
    with op.batch_alter_table("respuestas_intento") as batch_op:
        batch_op.alter_column(
            "respuesta_dada",
            existing_type=sa.String(1),
            type_=sa.Text(),
            nullable=False,
        )

    # ── 4. Datos adicionales de matemática ───────────────────────────────
    with op.batch_alter_table("examenes_matematica") as batch_op:
        batch_op.add_column(sa.Column("instrucciones", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("tipo_producto", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("contenido_json", sa.JSON(), nullable=True))

    # ── 5. Migrar textos de lectura ──────────────────────────────────────
    lecturas_rows = conn.execute(sa.text(
        "SELECT id, lectura, lecturas FROM examenes_lectura ORDER BY id"
    )).fetchall()
    for examen_id, lectura, lecturas_raw in lecturas_rows:
        ya = conn.execute(
            sa.text("SELECT COUNT(*) FROM textos_examen WHERE examen_lectura_id = :eid"),
            {"eid": examen_id},
        ).scalar()
        if ya:
            continue

        items = _parse(lecturas_raw)
        if not isinstance(items, list):
            items = []
        items = [
            t for t in items
            if isinstance(t, dict) and str(t.get("texto") or "").strip()
        ]
        if not items and isinstance(lectura, str) and lectura.strip():
            items = [{"titulo": "", "texto": lectura}]

        for orden, item in enumerate(items, start=1):
            titulo = item.get("titulo")
            conn.execute(sa.text("""
                INSERT INTO textos_examen
                    (examen_lectura_id, examen_matematica_id, orden, titulo, texto)
                VALUES
                    (:eid, NULL, :orden, :titulo, :texto)
            """), {
                "eid": examen_id,
                "orden": orden,
                "titulo": (str(titulo).strip() or None) if titulo else None,
                "texto": str(item.get("texto")),
            })

    # ── 6. Migrar situación problemática de matemática ───────────────────
    math_rows = conn.execute(sa.text(
        "SELECT id, situacion_problematica FROM examenes_matematica ORDER BY id"
    )).fetchall()
    for examen_id, situacion in math_rows:
        ya = conn.execute(
            sa.text("SELECT COUNT(*) FROM textos_examen WHERE examen_matematica_id = :eid"),
            {"eid": examen_id},
        ).scalar()
        if ya:
            continue
        if isinstance(situacion, str) and situacion.strip():
            conn.execute(sa.text("""
                INSERT INTO textos_examen
                    (examen_lectura_id, examen_matematica_id, orden, titulo, texto)
                VALUES
                    (NULL, :eid, 1, :titulo, :texto)
            """), {
                "eid": examen_id,
                "titulo": "Situación Problemática",
                "texto": situacion,
            })

    # ── 7. Enriquecer preguntas desde los JSON ───────────────────────────
    def _enriquecer(examen_id: int, columna: str, preguntas_raw, tabla_raw):
        preguntas = _parse(preguntas_raw)
        if not isinstance(preguntas, list):
            preguntas = []
        tabla = _parse(tabla_raw)
        if not isinstance(tabla, list):
            tabla = []
        tabla_map = {}
        for fila in tabla:
            if not isinstance(fila, dict):
                continue
            clave = fila.get("pregunta")
            if clave is None:
                continue
            tabla_map[clave] = fila
            tabla_map[str(clave)] = fila
            try:
                tabla_map[int(clave)] = fila
            except (TypeError, ValueError):
                pass

        for p in preguntas:
            if not isinstance(p, dict):
                continue
            num = p.get("numero")
            if num is None:
                continue
            info = tabla_map.get(num, {})

            opciones = {}
            for o in (p.get("opciones") or []):
                if not isinstance(o, dict):
                    continue
                letra = str(o.get("letra", "")).upper()
                texto = o.get("texto") or o.get("opcion") or o.get("alternativa") or ""
                if letra:
                    opciones[letra] = str(texto)

            tipo = str(p.get("tipo") or info.get("tipo") or "").strip().lower()
            if tipo not in ("cerrada", "abierta"):
                tipo = "cerrada" if any(str(v).strip() for v in opciones.values()) else "abierta"

            rc = str(info.get("respuesta_correcta") or "")[:1].upper() or None
            if tipo == "abierta":
                rc = None

            nivel = p.get("nivel") or info.get("nivel") or info.get("capacidad")
            desempeno_codigo = p.get("desempeno_codigo") or info.get("desempeno_codigo")
            desempeno = info.get("desempeno")
            contexto = p.get("contexto")
            respuesta_esperada = info.get("respuesta_esperada") or p.get("respuesta_esperada")
            espacio_respuesta = p.get("espacio_respuesta")
            criterio = p.get("criterio_evaluacion")

            conn.execute(sa.text(f"""
                UPDATE preguntas_examen SET
                    tipo = :tipo,
                    contexto = :contexto,
                    opcion_a = :a,
                    opcion_b = :b,
                    opcion_c = :c,
                    opcion_d = :d,
                    opcion_e = :e,
                    respuesta_correcta = :rc,
                    respuesta_esperada = :re,
                    espacio_respuesta = :esp,
                    nivel = :nivel,
                    desempeno_codigo = :dc,
                    desempeno_descripcion = :dd,
                    criterio_evaluacion = :crit,
                    justificacion = :just,
                    retroalimentacion_correcta = :retro_ok,
                    retroalimentacion_incorrecta = :retro_ko
                WHERE {columna} = :eid AND numero = :num
            """), {
                "tipo": tipo,
                "contexto": contexto,
                "a": opciones.get("A") or None,
                "b": opciones.get("B") or None,
                "c": opciones.get("C") or None,
                "d": opciones.get("D") or None,
                "e": opciones.get("E") or None,
                "rc": rc,
                "re": respuesta_esperada,
                "esp": espacio_respuesta,
                "nivel": str(nivel)[:20] if nivel else None,
                "dc": str(desempeno_codigo)[:50] if desempeno_codigo else None,
                "dd": desempeno,
                "crit": criterio,
                "just": info.get("justificacion"),
                "retro_ok": info.get("retroalimentacion_correcta"),
                "retro_ko": info.get("retroalimentacion_incorrecta"),
                "eid": examen_id,
                "num": num,
            })

    for examen_id, preguntas_raw, tabla_raw in conn.execute(sa.text(
        "SELECT id, preguntas, tabla_respuestas FROM examenes_lectura ORDER BY id"
    )).fetchall():
        _enriquecer(examen_id, "examen_lectura_id", preguntas_raw, tabla_raw)

    for examen_id, preguntas_raw, tabla_raw in conn.execute(sa.text(
        "SELECT id, preguntas, tabla_respuestas FROM examenes_matematica ORDER BY id"
    )).fetchall():
        _enriquecer(examen_id, "examen_matematica_id", preguntas_raw, tabla_raw)

    # Normalizar cadenas vacías a NULL e inferir tipo en filas sin JSON.
    for col in ("opcion_a", "opcion_b", "opcion_c", "opcion_d", "opcion_e"):
        conn.execute(sa.text(f"UPDATE preguntas_examen SET {col} = NULL WHERE {col} = ''"))
    conn.execute(sa.text(
        "UPDATE preguntas_examen SET respuesta_correcta = NULL WHERE respuesta_correcta = ''"
    ))
    conn.execute(sa.text("""
        UPDATE preguntas_examen
        SET tipo = 'abierta'
        WHERE (respuesta_correcta IS NULL)
          AND (opcion_a IS NULL)
          AND (opcion_b IS NULL)
          AND (opcion_c IS NULL)
          AND (opcion_d IS NULL)
    """))

    # ── 8. Restricciones de unicidad ─────────────────────────────────────
    # Se agregan después del backfill para fallar de forma explícita si hubiera
    # números repetidos por examen.
    with op.batch_alter_table("preguntas_examen") as batch_op:
        batch_op.create_unique_constraint(
            "uq_pregunta_lectura_numero", ["examen_lectura_id", "numero"]
        )
        batch_op.create_unique_constraint(
            "uq_pregunta_matematica_numero", ["examen_matematica_id", "numero"]
        )

    # Índices de apoyo (MySQL ya crea uno por FK; se evita duplicarlo).
    existentes = _indices(conn, "preguntas_examen")
    if "ix_preguntas_examen_examen_lectura_id" not in existentes:
        op.create_index(
            "ix_preguntas_examen_examen_lectura_id", "preguntas_examen", ["examen_lectura_id"]
        )
    if "ix_preguntas_examen_examen_matematica_id" not in existentes:
        op.create_index(
            "ix_preguntas_examen_examen_matematica_id", "preguntas_examen", ["examen_matematica_id"]
        )


# =============================================================================
# Downgrade
# =============================================================================

def downgrade() -> None:
    conn = op.get_bind()

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

    # Reconstruir columnas legacy de lectura.
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

    # Reconstruir columnas legacy de matemática.
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

    # Quitar restricciones e índices.
    with op.batch_alter_table("preguntas_examen") as batch_op:
        batch_op.drop_constraint("uq_pregunta_lectura_numero", type_="unique")
        batch_op.drop_constraint("uq_pregunta_matematica_numero", type_="unique")

    existentes = _indices(conn, "preguntas_examen")
    if "ix_preguntas_examen_examen_lectura_id" in existentes:
        op.drop_index("ix_preguntas_examen_examen_lectura_id", table_name="preguntas_examen")
    if "ix_preguntas_examen_examen_matematica_id" in existentes:
        op.drop_index("ix_preguntas_examen_examen_matematica_id", table_name="preguntas_examen")

    # Preparar datos para volver a columnas no nullable / CHAR(1).
    for col in ("opcion_a", "opcion_b", "opcion_c", "opcion_d"):
        conn.execute(sa.text(f"UPDATE preguntas_examen SET {col} = '' WHERE {col} IS NULL"))
    conn.execute(sa.text(
        "UPDATE preguntas_examen SET respuesta_correcta = '' WHERE respuesta_correcta IS NULL"
    ))
    conn.execute(sa.text("""
        UPDATE respuestas_intento
        SET respuesta_dada = SUBSTR(respuesta_dada, 1, 1)
        WHERE LENGTH(respuesta_dada) > 1
    """))

    with op.batch_alter_table("respuestas_intento") as batch_op:
        batch_op.alter_column(
            "respuesta_dada",
            existing_type=sa.Text(),
            type_=sa.String(1),
            nullable=False,
        )

    with op.batch_alter_table("preguntas_examen") as batch_op:
        batch_op.alter_column("opcion_a", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("opcion_b", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("opcion_c", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("opcion_d", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("respuesta_correcta", existing_type=sa.String(1), nullable=False)
        batch_op.drop_column("criterio_evaluacion")
        batch_op.drop_column("opcion_e")
        batch_op.drop_column("espacio_respuesta")
        batch_op.drop_column("respuesta_esperada")
        batch_op.drop_column("contexto")
        batch_op.drop_column("tipo")

    with op.batch_alter_table("examenes_matematica") as batch_op:
        batch_op.drop_column("contenido_json")
        batch_op.drop_column("tipo_producto")
        batch_op.drop_column("instrucciones")

    op.drop_index("ix_textos_examen_examen_matematica_id", table_name="textos_examen")
    op.drop_index("ix_textos_examen_examen_lectura_id", table_name="textos_examen")
    op.drop_index("ix_textos_examen_id", table_name="textos_examen")
    op.drop_table("textos_examen")

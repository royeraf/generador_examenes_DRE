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
3. Reconstruye las preguntas normalizadas desde los JSON ``preguntas`` y
   ``tabla_respuestas`` (incluye la 5.ª alternativa de MatSistem). Empareja
   por orden y renumera 1..N por examen para corregir números duplicados.
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

    # ── 0. Codificación ──────────────────────────────────────────────────
    # Producción usa latin1 por herencia, pero las preguntas de matemática
    # contienen símbolos como π o ≈. Las tablas normalizadas y las respuestas
    # deben poder almacenar UTF-8 completo. La conversión es segura para los
    # datos latin1 existentes (acentos y ñ).
    for tabla in (
        "preguntas_examen", "textos_examen", "respuestas_intento",
        "examenes_lectura", "examenes_matematica",
    ):
        if sa.inspect(conn).has_table(tabla):
            conn.execute(sa.text(
                f"ALTER TABLE {tabla} CONVERT TO CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci"
            ))

    # ── 1. textos_examen ─────────────────────────────────────────────────
    # Producción ya tenía esta tabla creada por un intento previo de
    # normalización, aunque la revisión de Alembic no estuviera marcada.
    # Se reutiliza si existe para no fallar con "table already exists".
    if not sa.inspect(conn).has_table("textos_examen"):
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
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
        )

    indices_textos = _indices(conn, "textos_examen")
    if "ix_textos_examen_id" not in indices_textos:
        op.create_index("ix_textos_examen_id", "textos_examen", ["id"])
    if "ix_textos_examen_examen_lectura_id" not in indices_textos:
        op.create_index("ix_textos_examen_examen_lectura_id", "textos_examen", ["examen_lectura_id"])
    if "ix_textos_examen_examen_matematica_id" not in indices_textos:
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

    # ── 7. Reconstruir preguntas desde los JSON ──────────────────────────
    # Se emparejan las filas existentes con las preguntas del JSON por orden de
    # ``id`` y se renumera 1..N por examen. Esto corrige dos problemas reales de
    # datos antiguos: números repetidos y actualizaciones cruzadas cuando había
    # duplicados (el UPDATE por ``numero`` afectaba a todas las filas iguales).
    def _merge(nuevo, actual):
        if nuevo is None:
            return actual
        if isinstance(nuevo, str) and not nuevo.strip():
            return actual
        return nuevo

    def _sincronizar(examen_id: int, columna: str, preguntas_raw, tabla_raw):
        preguntas = _parse(preguntas_raw)
        if not isinstance(preguntas, list):
            preguntas = []
        preguntas = [p for p in preguntas if isinstance(p, dict)]

        tabla = _parse(tabla_raw)
        if not isinstance(tabla, list):
            tabla = []
        tabla = [t for t in tabla if isinstance(t, dict)]

        tabla_map = {}
        for fila in tabla:
            clave = fila.get("pregunta")
            if clave is None:
                continue
            tabla_map[clave] = fila
            tabla_map[str(clave)] = fila
            try:
                tabla_map[int(clave)] = fila
            except (TypeError, ValueError):
                pass

        filas = conn.execute(sa.text(f"""
            SELECT id, enunciado, tipo, contexto, opcion_a, opcion_b, opcion_c,
                   opcion_d, opcion_e, respuesta_correcta, respuesta_esperada,
                   espacio_respuesta, nivel, desempeno_codigo, desempeno_descripcion,
                   criterio_evaluacion, justificacion,
                   retroalimentacion_correcta, retroalimentacion_incorrecta
            FROM preguntas_examen
            WHERE {columna} = :eid
            ORDER BY id
        """), {"eid": examen_id}).fetchall()

        # Los JSON de preguntas y tabla suelen ser arrays paralelos. Si sus
        # longitudes difieren, se usa el número original como respaldo.
        usar_indice = len(preguntas) == len(tabla)
        otra_columna = (
            "examen_matematica_id" if columna == "examen_lectura_id"
            else "examen_lectura_id"
        )

        for indice, p in enumerate(preguntas, start=1):
            actual = filas[indice - 1] if indice <= len(filas) else None
            info = (
                tabla[indice - 1]
                if usar_indice and indice <= len(tabla)
                else tabla_map.get(p.get("numero"), {})
            )

            opciones = {}
            for o in (p.get("opciones") or []):
                if not isinstance(o, dict):
                    continue
                letra = str(o.get("letra", "")).upper()
                texto = o.get("texto") or o.get("opcion") or o.get("alternativa") or ""
                if letra:
                    opciones[letra] = str(texto)

            tipo_nuevo = str(p.get("tipo") or info.get("tipo") or "").strip().lower()
            tipo_actual = str(actual[2] or "").strip().lower() if actual else ""
            if tipo_nuevo in ("cerrada", "abierta"):
                tipo = tipo_nuevo
            elif tipo_actual in ("cerrada", "abierta"):
                tipo = tipo_actual
            else:
                tipo = "cerrada" if any(str(v).strip() for v in opciones.values()) else "abierta"

            rc = str(info.get("respuesta_correcta") or "").strip()[:1].upper() or None
            rc = None if tipo == "abierta" else _merge(
                rc, actual[9] if actual else None
            )

            nivel = p.get("nivel") or info.get("nivel") or info.get("capacidad")
            nivel = _merge(str(nivel)[:20] if nivel else None, actual[12] if actual else None)
            dc = p.get("desempeno_codigo") or info.get("desempeno_codigo")
            dc = _merge(str(dc)[:50] if dc else None, actual[13] if actual else None)

            valores = {
                "num": indice,
                "enunciado": _merge(str(p.get("enunciado") or ""), actual[1] if actual else None) or "",
                "tipo": tipo,
                "contexto": _merge(p.get("contexto"), actual[3] if actual else None),
                "a": _merge(opciones.get("A"), actual[4] if actual else None),
                "b": _merge(opciones.get("B"), actual[5] if actual else None),
                "c": _merge(opciones.get("C"), actual[6] if actual else None),
                "d": _merge(opciones.get("D"), actual[7] if actual else None),
                "e": _merge(opciones.get("E"), actual[8] if actual else None),
                "rc": rc,
                "re": _merge(
                    info.get("respuesta_esperada") or p.get("respuesta_esperada"),
                    actual[10] if actual else None,
                ),
                "esp": _merge(p.get("espacio_respuesta"), actual[11] if actual else None),
                "nivel": nivel,
                "dc": dc,
                "dd": _merge(info.get("desempeno"), actual[14] if actual else None),
                "crit": _merge(p.get("criterio_evaluacion"), actual[15] if actual else None),
                "just": _merge(info.get("justificacion"), actual[16] if actual else None),
                "retro_ok": _merge(
                    info.get("retroalimentacion_correcta"), actual[17] if actual else None
                ),
                "retro_ko": _merge(
                    info.get("retroalimentacion_incorrecta"), actual[18] if actual else None
                ),
            }

            if actual:
                valores["id"] = actual[0]
                conn.execute(sa.text("""
                    UPDATE preguntas_examen SET
                        numero = :num, enunciado = :enunciado, tipo = :tipo,
                        contexto = :contexto, opcion_a = :a, opcion_b = :b,
                        opcion_c = :c, opcion_d = :d, opcion_e = :e,
                        respuesta_correcta = :rc, respuesta_esperada = :re,
                        espacio_respuesta = :esp, nivel = :nivel,
                        desempeno_codigo = :dc, desempeno_descripcion = :dd,
                        criterio_evaluacion = :crit, justificacion = :just,
                        retroalimentacion_correcta = :retro_ok,
                        retroalimentacion_incorrecta = :retro_ko
                    WHERE id = :id
                """), valores)
            else:
                valores["eid"] = examen_id
                conn.execute(sa.text(f"""
                    INSERT INTO preguntas_examen
                        ({columna}, {otra_columna}, numero, enunciado, tipo, contexto,
                         opcion_a, opcion_b, opcion_c, opcion_d, opcion_e,
                         respuesta_correcta, respuesta_esperada, espacio_respuesta,
                         nivel, desempeno_codigo, desempeno_descripcion,
                         criterio_evaluacion, justificacion,
                         retroalimentacion_correcta, retroalimentacion_incorrecta)
                    VALUES
                        (:eid, NULL, :num, :enunciado, :tipo, :contexto,
                         :a, :b, :c, :d, :e, :rc, :re, :esp, :nivel, :dc, :dd,
                         :crit, :just, :retro_ok, :retro_ko)
                """), valores)

        # Filas normalizadas que no tienen contraparte en el JSON: conservarlas,
        # pero renumerarlas para cumplir la restricción de unicidad.
        for numero, fila in enumerate(filas[len(preguntas):], start=len(preguntas) + 1):
            conn.execute(
                sa.text("UPDATE preguntas_examen SET numero = :num WHERE id = :id"),
                {"num": numero, "id": fila[0]},
            )

    for examen_id, preguntas_raw, tabla_raw in conn.execute(sa.text(
        "SELECT id, preguntas, tabla_respuestas FROM examenes_lectura ORDER BY id"
    )).fetchall():
        _sincronizar(examen_id, "examen_lectura_id", preguntas_raw, tabla_raw)

    for examen_id, preguntas_raw, tabla_raw in conn.execute(sa.text(
        "SELECT id, preguntas, tabla_respuestas FROM examenes_matematica ORDER BY id"
    )).fetchall():
        _sincronizar(examen_id, "examen_matematica_id", preguntas_raw, tabla_raw)

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
    # Se agregan después del backfill; la renumeración anterior garantiza que
    # no existan números repetidos por examen.
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

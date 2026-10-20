"""Serializadores de exámenes.

Componen el contrato JSON que consume el frontend (``lectura``, ``lecturas``,
``preguntas`` y ``tabla_respuestas``) a partir de las tablas normalizadas
``textos_examen`` y ``preguntas_examen``.

La fuente de verdad son las tablas; este módulo solo adapta la salida para no
romper a los clientes que todavía esperan el formato anterior.
"""
from typing import Iterable


def _ordenados_textos(textos: Iterable) -> list:
    return sorted(textos or [], key=lambda t: (t.orden or 0, t.id or 0))


def _ordenadas_preguntas(preguntas: Iterable) -> list:
    return sorted(preguntas or [], key=lambda p: (p.numero or 0, p.id or 0))


def lecturas_dict(textos: Iterable) -> list[dict]:
    """Devuelve ``[{titulo, texto}]`` ordenado por ``orden``."""
    return [
        {"titulo": (t.titulo or ""), "texto": (t.texto or "")}
        for t in _ordenados_textos(textos)
    ]


def texto_concatenado(textos: Iterable) -> str:
    """Texto único para compatibilidad.

    Con un solo texto devuelve su cuerpo. Con varios, concatena con el mismo
    formato que usaba LectoSistem (``TEXTO n: título`` + separador).
    """
    textos = _ordenados_textos(textos)
    if not textos:
        return ""
    if len(textos) == 1:
        return textos[0].texto or ""
    partes = []
    for indice, t in enumerate(textos, start=1):
        titulo = (t.titulo or "").strip()
        header = f"TEXTO {indice}: {titulo}" if titulo else f"TEXTO {indice}"
        partes.append(f"{'─' * 40}\n{header}\n{'─' * 40}\n{t.texto or ''}")
    return "\n\n".join(partes)


def texto_plano(textos: Iterable) -> str:
    """Une los textos con saltos de línea (para situación problemática)."""
    return "\n\n".join((t.texto or "") for t in _ordenados_textos(textos))


def _opciones(pregunta) -> list[dict]:
    letras = (
        ("A", pregunta.opcion_a),
        ("B", pregunta.opcion_b),
        ("C", pregunta.opcion_c),
        ("D", pregunta.opcion_d),
        ("E", pregunta.opcion_e),
    )
    correcta = (pregunta.respuesta_correcta or "").upper()
    opciones = []
    for letra, texto in letras:
        if texto is None or str(texto).strip() == "":
            continue
        opciones.append(
            {
                "letra": letra,
                "valor": letra,
                "texto": texto,
                "es_correcta": correcta == letra,
            }
        )
    return opciones


def _pregunta_dict(pregunta) -> dict:
    return {
        "numero": pregunta.numero,
        "enunciado": pregunta.enunciado,
        "opciones": _opciones(pregunta),
        "desempeno_codigo": pregunta.desempeno_codigo or "",
        "nivel": pregunta.nivel or "",
        "tipo": pregunta.tipo or "cerrada",
        "contexto": pregunta.contexto,
        "respuesta_esperada": pregunta.respuesta_esperada,
        "espacio_respuesta": pregunta.espacio_respuesta,
    }


def _fila_tabla(pregunta) -> dict:
    return {
        "pregunta": pregunta.numero,
        "desempeno": pregunta.desempeno_descripcion or pregunta.desempeno_codigo or "",
        "nivel": pregunta.nivel or "",
        "respuesta_correcta": pregunta.respuesta_correcta or "",
        "respuesta_esperada": pregunta.respuesta_esperada,
        "justificacion": pregunta.justificacion or "",
        "retroalimentacion_correcta": pregunta.retroalimentacion_correcta or "",
        "retroalimentacion_incorrecta": pregunta.retroalimentacion_incorrecta or "",
        "tipo": pregunta.tipo or "cerrada",
    }


def serializar_examen_lectura(examen, textos: Iterable, preguntas: Iterable) -> dict:
    textos = _ordenados_textos(textos)
    preguntas = _ordenadas_preguntas(preguntas)
    preguntas_out = [_pregunta_dict(p) for p in preguntas]
    return {
        "id": examen.id,
        "docente_id": examen.docente_id,
        "grado_id": examen.grado_id,
        "fecha_creacion": examen.fecha_creacion,
        "titulo": examen.titulo,
        "grado_nombre": examen.grado_nombre,
        "nivel_dificultad": examen.nivel_dificultad,
        "modelo_ia": examen.modelo_ia,
        "saludo": examen.saludo,
        "instrucciones": examen.instrucciones,
        "lectura": texto_concatenado(textos),
        "lecturas": lecturas_dict(textos),
        "preguntas": preguntas_out,
        "tabla_respuestas": [_fila_tabla(p) for p in preguntas],
        "desempenos_usados": examen.desempenos_usados,
        "total_preguntas": len(preguntas_out),
    }


def serializar_examen_matematica(examen, textos: Iterable, preguntas: Iterable) -> dict:
    textos = _ordenados_textos(textos)
    preguntas = _ordenadas_preguntas(preguntas)
    preguntas_out = [_pregunta_dict(p) for p in preguntas]
    return {
        "id": examen.id,
        "docente_id": examen.docente_id,
        "grado_id": examen.grado_id,
        "competencia_id": examen.competencia_id,
        "fecha_creacion": examen.fecha_creacion,
        "titulo": examen.titulo,
        "grado_nombre": examen.grado_nombre,
        "nivel_dificultad": examen.nivel_dificultad,
        "modelo_ia": examen.modelo_ia,
        "saludo": examen.saludo,
        "instrucciones": examen.instrucciones,
        "tipo_producto": examen.tipo_producto,
        "contenido_json": examen.contenido_json,
        "situacion_problematica": texto_plano(textos),
        "lecturas": lecturas_dict(textos),
        "preguntas": preguntas_out,
        "tabla_respuestas": [_fila_tabla(p) for p in preguntas],
        "desempenos_usados": examen.desempenos_usados,
        "total_preguntas": len(preguntas_out),
    }

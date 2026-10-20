"""
Escala de calificación CNEB (Currículo Nacional de Educación Básica).

Convierte el puntaje porcentual de un examen (0-100) a:
- Nota vigesimal (0-20) con redondeo half-up.
- Nivel literal CNEB: AD / A / B / C.

Referencia: "Tabla Comparativa Referencial de Calificaciones" del MINEDU.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


# ── Tabla de referencia ────────────────────────────────────────────────────────
# Ordenada de mayor a menor logro. Es la fuente de verdad para la leyenda del
# frontend y para la clasificación.
ESCALA_CNEB = [
    {
        "codigo": "AD",
        "nombre": "Logro Destacado",
        "significado": (
            "El estudiante demuestra un aprendizaje que supera las expectativas "
            "y los estándares previstos para el periodo."
        ),
        "min": 18,
        "max": 20,
    },
    {
        "codigo": "A",
        "nombre": "Logro Esperado",
        "significado": (
            "El estudiante demuestra el manejo adecuado de las tareas y cumple "
            "satisfactoriamente con las competencias esperadas."
        ),
        "min": 15,
        "max": 17,
    },
    {
        "codigo": "B",
        "nombre": "En Proceso",
        "significado": (
            "El estudiante se encuentra próximo al nivel esperado, pero requiere "
            "acompañamiento o mayor tiempo para lograrlo."
        ),
        "min": 11,
        "max": 14,
    },
    {
        "codigo": "C",
        "nombre": "En Inicio",
        "significado": (
            "El estudiante muestra un progreso mínimo, evidencia dificultades "
            "significativas y necesita una intervención docente directa."
        ),
        "min": 0,
        "max": 10,
    },
]

_NIVELES = {item["codigo"]: item for item in ESCALA_CNEB}


def porcentaje_a_nota(puntaje_100: Optional[float]) -> Optional[float]:
    """Convierte un puntaje porcentual (0-100) a nota vigesimal (0-20).

    Redondeo half-up (0.5 hacia arriba): 74% -> 14.8 -> 15, 72% -> 14.4 -> 14.
    Se usa Decimal porque round() de Python aplica redondeo bancario.
    """
    if puntaje_100 is None:
        return None
    puntaje = max(0.0, min(100.0, float(puntaje_100)))
    nota = Decimal(str(puntaje)) / Decimal("5")
    return float(nota.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def nota_a_nivel(nota: float) -> str:
    """Devuelve el literal CNEB (AD/A/B/C) correspondiente a una nota vigesimal."""
    if nota >= 18:
        return "AD"
    if nota >= 15:
        return "A"
    if nota >= 11:
        return "B"
    return "C"


def clasificar(puntaje_100: Optional[float]) -> dict:
    """Devuelve la clasificación CNEB completa para un puntaje porcentual.

    Retorna un dict con: nota_vigesimal, nivel_cneb, nivel_cneb_nombre y
    nivel_cneb_significado. Todos los campos son None si no hay puntaje.
    """
    nota = porcentaje_a_nota(puntaje_100)
    if nota is None:
        return {
            "nota_vigesimal": None,
            "nivel_cneb": None,
            "nivel_cneb_nombre": None,
            "nivel_cneb_significado": None,
        }
    nivel = nota_a_nivel(nota)
    detalle = _NIVELES[nivel]
    return {
        "nota_vigesimal": nota,
        "nivel_cneb": nivel,
        "nivel_cneb_nombre": detalle["nombre"],
        "nivel_cneb_significado": detalle["significado"],
    }

"""
Rutas de la escala de calificación CNEB.
"""
from fastapi import APIRouter, Depends

from app.models.usuario import Usuario
from app.api.dependencies import get_current_active_user
from app.core.escala_cneb import ESCALA_CNEB

router = APIRouter()


@router.get("/escala-calificacion")
async def escala_calificacion(
    _: Usuario = Depends(get_current_active_user),
):
    """Devuelve la tabla referencial de calificaciones CNEB (AD/A/B/C).

    Usada por el frontend para pintar la leyenda y por otros módulos que
    necesiten la escala de forma centralizada.
    """
    return {
        "escala": [
            {
                **nivel,
                "rango": f"{nivel['min']:02d} - {nivel['max']:02d}",
            }
            for nivel in ESCALA_CNEB
        ]
    }

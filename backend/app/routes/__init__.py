"""
Router Central - Punto de entrada para todos los routers de la API.

Este módulo centraliza el registro de todos los routers de la aplicación,
facilitando la escalabilidad y mantenimiento del código.

Estructura de módulos:
- comunicacion/: Endpoints para el módulo LectoSistem (comprensión lectora)
- matematica/: Endpoints para el módulo MatSistem
- admin/: Endpoints de administración general
- shared/: Endpoints compartidos entre módulos
"""

from fastapi import APIRouter

# Importar routers existentes (manteniendo compatibilidad)
from app.routes.preguntas import router as preguntas_router
from app.routes.desempenos import router as desempenos_router
from app.routes.admin import router as admin_router
from app.routes.matematica import router as matematica_router


def create_api_router() -> APIRouter:
    """
    Crea y configura el router principal de la API.
    
    Returns:
        APIRouter configurado con todos los sub-routers registrados.
    """
    api_router = APIRouter()
    
    # ==========================================================================
    # MÓDULO: COMUNICACIÓN (LectoSistem) - Comprensión Lectora
    # ==========================================================================
    api_router.include_router(
        preguntas_router,
        prefix="/preguntas",
        tags=["Preguntas - Comunicación"]
    )
    api_router.include_router(
        desempenos_router,
        prefix="/desempenos",
        tags=["Desempeños - Comunicación"]
    )
    
    # ==========================================================================
    # MÓDULO: MATEMÁTICA (MatSistem)
    # ==========================================================================
    api_router.include_router(
        matematica_router,
        prefix="/matematica",
        tags=["Matemática - MatSistem"]
    )
    
    # ==========================================================================
    # MÓDULO: ADMINISTRACIÓN
    # ==========================================================================
    api_router.include_router(
        admin_router,
        prefix="/admin",
        tags=["Administración"]
    )
    
    return api_router


# Router listo para usar
api_router = create_api_router()

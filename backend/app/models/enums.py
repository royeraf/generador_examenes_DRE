import enum
from typing import List


class RolCodigo(str, enum.Enum):
    """Roles disponibles en el sistema."""
    ESPECIALISTA_DRE_COMUNICACION = "especialista_dre_comunicacion"
    ESPECIALISTA_DRE_MATEMATICA = "especialista_dre_matematica"
    RESPONSABLE_UGEL = "responsable_ugel"
    DIRECTOR = "director"
    AUXILIAR = "auxiliar"
    DOCENTE = "docente"
    ESTUDIANTE = "estudiante"


class NivelLogro(str, enum.Enum):
    """Niveles de logro para evaluación de estudiantes."""
    PRE_INICIO = "pre_inicio"
    INICIO = "inicio"
    PROCESO = "proceso"
    SATISFACTORIO = "satisfactorio"
    DESTACADO = "destacado"


class EstadoIntento(str, enum.Enum):
    """Estado de un intento de examen."""
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    ABANDONADO = "abandonado"


# ── Módulos del sistema ────────────────────────────────────────────────────────

MODULO_LECTOSISTEM = "lectosistem"
MODULO_MATSISTEM = "matsistem"
MODULO_ASIGNACIONES = "asignaciones"
MODULO_CODIGOS_CLASE = "codigos_clase"
MODULO_METRICAS = "metricas"
MODULO_ADMIN_DESEMPENOS = "admin_desempenos"                          # acceso a AMBAS áreas
MODULO_ADMIN_DESEMPENOS_COMUNICACION = "admin_desempenos_comunicacion" # solo Comunicación
MODULO_ADMIN_DESEMPENOS_MATEMATICA = "admin_desempenos_matematica"     # solo Matemática
MODULO_ADMIN_UGELES = "admin_ugeles"
MODULO_ADMIN_INSTITUCIONES = "admin_instituciones"
MODULO_ADMIN_USUARIOS = "admin_usuarios"

MODULOS_DISPONIBLES: List[str] = [
    MODULO_LECTOSISTEM,
    MODULO_MATSISTEM,
    MODULO_ASIGNACIONES,
    MODULO_CODIGOS_CLASE,
    MODULO_METRICAS,
    MODULO_ADMIN_DESEMPENOS,
    MODULO_ADMIN_DESEMPENOS_COMUNICACION,
    MODULO_ADMIN_DESEMPENOS_MATEMATICA,
    MODULO_ADMIN_UGELES,
    MODULO_ADMIN_INSTITUCIONES,
    MODULO_ADMIN_USUARIOS,
]

_DRE_COMUN_MODULOS = [
    MODULO_LECTOSISTEM, MODULO_MATSISTEM, MODULO_ASIGNACIONES, MODULO_CODIGOS_CLASE,
    MODULO_METRICAS, MODULO_ADMIN_DESEMPENOS_COMUNICACION,
    MODULO_ADMIN_UGELES, MODULO_ADMIN_INSTITUCIONES, MODULO_ADMIN_USUARIOS,
]
_DRE_MAT_MODULOS = [
    MODULO_LECTOSISTEM, MODULO_MATSISTEM, MODULO_ASIGNACIONES, MODULO_CODIGOS_CLASE,
    MODULO_METRICAS, MODULO_ADMIN_DESEMPENOS_MATEMATICA,
    MODULO_ADMIN_UGELES, MODULO_ADMIN_INSTITUCIONES, MODULO_ADMIN_USUARIOS,
]

# Módulos habilitados por defecto según rol (cuando permisos_modulos es NULL)
ROLE_MODULOS_DEFAULT: dict[str, List[str]] = {
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION: _DRE_COMUN_MODULOS,
    RolCodigo.ESPECIALISTA_DRE_MATEMATICA: _DRE_MAT_MODULOS,
    RolCodigo.RESPONSABLE_UGEL: [MODULO_METRICAS, MODULO_ADMIN_INSTITUCIONES, MODULO_ADMIN_USUARIOS],
    RolCodigo.DIRECTOR: [
        MODULO_LECTOSISTEM, MODULO_MATSISTEM,
        MODULO_ASIGNACIONES, MODULO_CODIGOS_CLASE, MODULO_METRICAS, MODULO_ADMIN_USUARIOS,
    ],
    RolCodigo.AUXILIAR: [
        MODULO_LECTOSISTEM, MODULO_MATSISTEM,
        MODULO_ASIGNACIONES, MODULO_CODIGOS_CLASE, MODULO_METRICAS,
    ],
    RolCodigo.DOCENTE: [
        MODULO_LECTOSISTEM, MODULO_MATSISTEM,
        MODULO_ASIGNACIONES, MODULO_CODIGOS_CLASE, MODULO_METRICAS,
    ],
    RolCodigo.ESTUDIANTE: [],
}

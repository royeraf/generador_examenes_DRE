"""
Sistema de permisos basado en roles (RBAC).
Define qué roles tienen qué permisos y utilidades de scope.
"""
from app.models.enums import RolCodigo

# Roles con acceso de lectura/escritura de desempeños DRE
ROLES_DRE = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}

# Roles que administran la plataforma (equivalente al antiguo is_superuser)
ROLES_ADMIN = ROLES_DRE

# Mapa de permisos: permiso -> set de roles que lo tienen
PERMISOS: dict[str, set[RolCodigo]] = {
    # Gestión de contenido curricular DRE
    "manage_desempenos_lectura": {RolCodigo.ESPECIALISTA_DRE_COMUNICACION},
    "manage_desempenos_matematica": {RolCodigo.ESPECIALISTA_DRE_MATEMATICA},
    "manage_grados": ROLES_DRE,
    "manage_capacidades": {RolCodigo.ESPECIALISTA_DRE_COMUNICACION},
    "manage_competencias_mat": {RolCodigo.ESPECIALISTA_DRE_MATEMATICA},

    # Gestión organizacional
    "manage_ugel": ROLES_DRE,
    "manage_instituciones": ROLES_DRE | {RolCodigo.RESPONSABLE_UGEL},
    "manage_school": {RolCodigo.DIRECTOR} | ROLES_DRE | {RolCodigo.RESPONSABLE_UGEL},

    # Gestión de usuarios
    "create_users": ROLES_DRE | {RolCodigo.RESPONSABLE_UGEL, RolCodigo.DIRECTOR},
    "view_all_users": ROLES_DRE,
    "view_ugel_users": {RolCodigo.RESPONSABLE_UGEL},
    "view_school_users": {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR},

    # Exámenes
    "create_exams": {RolCodigo.DOCENTE, RolCodigo.AUXILIAR, RolCodigo.DIRECTOR},
    "assign_exams": {RolCodigo.DOCENTE, RolCodigo.AUXILIAR, RolCodigo.DIRECTOR},
    "take_exams": {RolCodigo.ESTUDIANTE},
    "view_exam_results": {RolCodigo.DOCENTE, RolCodigo.AUXILIAR, RolCodigo.DIRECTOR} | ROLES_DRE | {RolCodigo.RESPONSABLE_UGEL},

    # Métricas
    "view_all_metrics": ROLES_DRE,
    "view_ugel_metrics": {RolCodigo.RESPONSABLE_UGEL},
    "view_school_metrics": {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR},
    "view_own_metrics": {RolCodigo.DOCENTE, RolCodigo.ESTUDIANTE},

    # Códigos de clase
    "manage_codigos_clase": {RolCodigo.DOCENTE, RolCodigo.AUXILIAR, RolCodigo.DIRECTOR},
}


def tiene_permiso(rol_codigo: str, permiso: str) -> bool:
    """Verifica si un rol tiene un permiso específico."""
    roles_con_permiso = PERMISOS.get(permiso, set())
    return RolCodigo(rol_codigo) in roles_con_permiso


# Niveles jerárquicos por rol (menor = más alto en la jerarquía)
NIVEL_JERARQUIA: dict[RolCodigo, int] = {
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION: 1,
    RolCodigo.ESPECIALISTA_DRE_MATEMATICA: 1,
    RolCodigo.RESPONSABLE_UGEL: 2,
    RolCodigo.DIRECTOR: 3,
    RolCodigo.AUXILIAR: 4,
    RolCodigo.DOCENTE: 5,
    RolCodigo.ESTUDIANTE: 6,
}


def puede_crear_rol(creador_rol: str, nuevo_rol: str) -> bool:
    """Verifica si un rol puede crear usuarios de otro rol (solo puede crear roles de nivel inferior)."""
    try:
        nivel_creador = NIVEL_JERARQUIA[RolCodigo(creador_rol)]
        nivel_nuevo = NIVEL_JERARQUIA[RolCodigo(nuevo_rol)]
        return nivel_creador < nivel_nuevo
    except (ValueError, KeyError):
        return False

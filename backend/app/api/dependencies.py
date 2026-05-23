from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import settings
from app.repositories.usuario_repository import usuario_repository
from app.repositories.estudiante_repository import estudiante_repository
from app.models.usuario import Usuario
from app.models.estudiante import Estudiante
from app.models.enums import RolCodigo
from app.schemas.token import TokenPayload
from typing import Union

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> Union[Usuario, Estudiante]:
    """Obtiene el usuario autenticado. Usa el campo 'rol' del JWT para enrutar a la tabla correcta."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str = payload.get("sub")
        rol: str = payload.get("rol", "")
        if sub is None:
            raise credentials_exception
        token_data = TokenPayload(sub=sub)
    except JWTError:
        raise credentials_exception

    if rol == RolCodigo.ESTUDIANTE:
        user = await estudiante_repository.get_by_login(db, identifier=token_data.sub)
    else:
        user = await usuario_repository.get_by_login(db, identifier=token_data.sub)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user


def require_role(*roles: RolCodigo) -> Callable:
    """
    Dependency factory que valida que el usuario tenga uno de los roles indicados.
    Uso: Depends(require_role(RolCodigo.DOCENTE, RolCodigo.DIRECTOR))
    """
    async def _check_role(
        current_user: Usuario = Depends(get_current_active_user),
    ) -> Usuario:
        if current_user.rol_codigo not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return current_user
    return _check_role


def require_permission(permiso: str) -> Callable:
    """
    Dependency factory que valida que el usuario tenga el permiso indicado.
    Uso: Depends(require_permission("create_exams"))
    """
    from app.core.permissions import tiene_permiso

    async def _check_permission(
        current_user: Usuario = Depends(get_current_active_user),
    ) -> Usuario:
        if not tiene_permiso(current_user.rol_codigo, permiso):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return current_user
    return _check_permission


# Aliases de compatibilidad con el código anterior
async def get_current_superuser(
    current_user: Usuario = Depends(get_current_active_user),
) -> Usuario:
    """Alias de compatibilidad: requiere rol de especialista DRE."""
    from app.core.permissions import ROLES_ADMIN
    if RolCodigo(current_user.rol_codigo) not in ROLES_ADMIN:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    return current_user


# Dependency shortcuts para los roles más usados
get_dre_user = require_role(
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION,
    RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
)

get_dre_comunicacion = require_role(RolCodigo.ESPECIALISTA_DRE_COMUNICACION)
get_dre_matematica = require_role(RolCodigo.ESPECIALISTA_DRE_MATEMATICA)

get_docente_user = require_role(
    RolCodigo.DOCENTE,
    RolCodigo.AUXILIAR,
    RolCodigo.DIRECTOR,
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION,
    RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
    RolCodigo.RESPONSABLE_UGEL,
)

async def get_estudiante_user(
    current_user: Union[Usuario, Estudiante] = Depends(get_current_active_user),
) -> Estudiante:
    """Dependency que garantiza que el usuario autenticado es un Estudiante."""
    if not isinstance(current_user, Estudiante):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
    return current_user


def require_modulo(modulo: str) -> Callable:
    """
    Dependency factory: verifica que el usuario tenga acceso al módulo indicado.
    Combina rol + permisos_modulos del usuario.
    Uso: Depends(require_modulo("lectosistem"))
    """
    async def _check_modulo(
        current_user: Usuario = Depends(get_current_active_user),
    ) -> Usuario:
        if not current_user.tiene_modulo(modulo):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sin acceso al módulo '{modulo}'",
            )
        return current_user
    return _check_modulo

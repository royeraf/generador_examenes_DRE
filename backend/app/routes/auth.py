import uuid
from datetime import timedelta, datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, settings, verify_password, get_password_hash
from app.core.request_meta import get_client_ip, parse_user_agent
from app.services.usuario_service import usuario_service
from app.services.estudiante_service import estudiante_service
from app.services.matricula_service import get_matricula_activa
from app.schemas.usuario import Usuario, MatriculaSchema
from app.schemas.token import Token
from app.api.dependencies import get_current_active_user, oauth2_scheme
from app.models.usuario import Usuario as UsuarioModel
from app.models.estudiante import Estudiante as EstudianteModel
from app.models.sesion import SesionAcceso
from app.models.enums import RolCodigo


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=4, max_length=72)


router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Login con DNI (docentes/directores) o código de estudiante (EST0001).
    Retorna JWT con sub=identificador y rol=codigo_rol.
    """
    user_agent = request.headers.get("user-agent")
    ip = get_client_ip(request)
    meta = parse_user_agent(user_agent)
    now = datetime.now(timezone.utc)

    def _base_sesion(**kwargs) -> SesionAcceso:
        return SesionAcceso(
            ip=ip,
            user_agent=user_agent,
            dispositivo=meta["dispositivo"],
            sistema_operativo=meta["sistema_operativo"],
            navegador=meta["navegador"],
            es_movil=meta["es_movil"],
            login_at=now,
            last_activity=now,
            **kwargs,
        )

    usuario = await usuario_service.authenticate(
        db, identifier=form_data.username, password=form_data.password
    )
    tipo_usuario = "usuario"
    if not usuario:
        usuario = await estudiante_service.authenticate(
            db, identifier=form_data.username, password=form_data.password
        )
        tipo_usuario = "estudiante"

    if not usuario:
        # Auditar intento fallido (commit explícito: get_db haría rollback al lanzar HTTPException)
        db.add(_base_sesion(
            jti=None,
            exito=False,
            motivo="credenciales",
            identificador=form_data.username,
            is_active=False,
        ))
        await db.commit()
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    if not usuario.is_active:
        db.add(_base_sesion(
            jti=None,
            exito=False,
            motivo="inactivo",
            tipo_usuario=tipo_usuario,
            usuario_id=usuario.id,
            identificador=usuario.codigo_estudiante or usuario.dni or form_data.username,
            nombres=usuario.nombres,
            apellidos=usuario.apellidos,
            rol_codigo=usuario.rol_codigo,
            institucion_educativa_id=getattr(usuario, "institucion_educativa_id", None),
            ugel_id=getattr(usuario, "ugel_id", None),
            is_active=False,
        ))
        await db.commit()
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    identifier = usuario.codigo_estudiante or usuario.dni
    jti = uuid.uuid4().hex
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)

    # Registrar sesión activa
    db.add(_base_sesion(
        jti=jti,
        exito=True,
        tipo_usuario=tipo_usuario,
        usuario_id=usuario.id,
        identificador=identifier,
        nombres=usuario.nombres,
        apellidos=usuario.apellidos,
        rol_codigo=usuario.rol_codigo,
        institucion_educativa_id=getattr(usuario, "institucion_educativa_id", None),
        ugel_id=getattr(usuario, "ugel_id", None),
        is_active=True,
    ))
    usuario.ultimo_acceso = now

    return {
        "access_token": create_access_token(
            data={"sub": identifier, "rol": usuario.rol_codigo, "jti": jti},
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: UsuarioModel = Depends(get_current_active_user),
) -> Any:
    """Cierra la sesión actual marcando el registro de monitoreo."""
    jti: Optional[str] = None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        jti = payload.get("jti")
    except JWTError:
        jti = None

    if jti:
        await db.execute(
            update(SesionAcceso)
            .where(SesionAcceso.jti == jti)
            .values(logout_at=datetime.now(timezone.utc), is_active=False)
        )
    return {"message": "Sesión cerrada"}


@router.get("/me", response_model=Usuario)
async def read_users_me(
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_active_user),
) -> Any:
    """Retorna el perfil del usuario autenticado."""
    response = Usuario.model_validate(current_user)
    if current_user.rol_codigo == RolCodigo.ESTUDIANTE:
        matricula = await get_matricula_activa(db, current_user.id)
        if matricula:
            response.matricula_activa = MatriculaSchema(
                id=matricula.id,
                año_escolar=matricula.año_escolar,
                grado_id=matricula.grado_id,
                grado_nombre=matricula.grado.nombre if matricula.grado else None,
                seccion=matricula.seccion,
                is_active=matricula.is_active,
            )
    return response


@router.put("/me/password")
async def change_my_password(
    data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_active_user),
) -> Any:
    """Cambia la contraseña del usuario autenticado."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    current_user.password_hash = get_password_hash(data.new_password)
    db.add(current_user)
    await db.commit()
    return {"message": "Contraseña actualizada correctamente"}

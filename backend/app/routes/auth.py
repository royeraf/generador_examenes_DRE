from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, settings, verify_password, get_password_hash
from app.services.usuario_service import usuario_service
from app.services.estudiante_service import estudiante_service
from app.services.matricula_service import get_matricula_activa
from app.schemas.usuario import Usuario, MatriculaSchema
from app.schemas.token import Token
from app.api.dependencies import get_current_active_user
from app.models.usuario import Usuario as UsuarioModel
from app.models.estudiante import Estudiante as EstudianteModel
from app.models.enums import RolCodigo


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=4, max_length=72)


router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Login con DNI (docentes/directores) o código de estudiante (EST0001).
    Retorna JWT con sub=identificador y rol=codigo_rol.
    """
    usuario = await usuario_service.authenticate(
        db, identifier=form_data.username, password=form_data.password
    )
    if not usuario:
        usuario = await estudiante_service.authenticate(
            db, identifier=form_data.username, password=form_data.password
        )
    if not usuario:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    if not usuario.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    identifier = usuario.codigo_estudiante or usuario.dni
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    return {
        "access_token": create_access_token(
            data={"sub": identifier, "rol": usuario.rol_codigo},
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
    }


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

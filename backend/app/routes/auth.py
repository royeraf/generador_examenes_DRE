from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, settings, verify_password, get_password_hash
from app.services.usuario_service import usuario_service
from app.schemas.usuario import Usuario
from app.schemas.token import Token
from app.api.dependencies import get_current_active_user
from app.models.usuario import Usuario as UsuarioModel


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
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    if not usuario.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    # Identificador principal para el token: DNI o código de estudiante
    identifier = usuario.dni or usuario.codigo_estudiante
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
    current_user: UsuarioModel = Depends(get_current_active_user),
) -> Any:
    """Retorna el perfil del usuario autenticado."""
    return current_user


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

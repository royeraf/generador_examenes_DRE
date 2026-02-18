from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, settings, verify_password, get_password_hash
from app.services.docente_service import docente_service
from app.schemas.docente import Docente
from app.schemas.token import Token
from app.api.dependencies import get_current_active_user
from app.models.docente import Docente as DocenteModel


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=72)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    docente = await docente_service.authenticate(
        db, dni=form_data.username, password=form_data.password
    )
    if not docente:
        raise HTTPException(status_code=400, detail="DNI o contraseña incorrectos")
    elif not docente.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    return {
        "access_token": create_access_token(
            data={"sub": docente.dni}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=Docente)
async def read_users_me(
    current_user: DocenteModel = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me/password")
async def change_my_password(
    data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
) -> Any:
    """
    Change current user's own password.
    """
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    current_user.password_hash = get_password_hash(data.new_password)
    db.add(current_user)
    await db.commit()
    return {"message": "Contraseña actualizada correctamente"}

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, settings
from app.services.docente_service import docente_service
from app.schemas.docente import Docente, DocenteCreate
from app.schemas.token import Token
from app.api.dependencies import get_current_active_user
from app.models.docente import Docente as DocenteModel

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
        raise HTTPException(status_code=400, detail="Incorrect DNI or password")
    elif not docente.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    return {
        "access_token": create_access_token(
            data={"sub": docente.dni}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=Docente)
async def register_docente(
    docente_in: DocenteCreate,
    db: AsyncSession = Depends(get_db) 
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    try:
        docente = await docente_service.create_docente(db, docente_in)
        return docente
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

@router.get("/me", response_model=Docente)
async def read_users_me(
    current_user: DocenteModel = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

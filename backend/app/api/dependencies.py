from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import settings
from app.repositories.docente_repository import docente_repository
from app.models.docente import Docente
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Docente:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        dni: str = payload.get("sub")
        if dni is None:
            raise credentials_exception
        token_data = TokenPayload(sub=dni)
    except JWTError:
        raise credentials_exception

    user = await docente_repository.get_by_dni(db, dni=token_data.sub)
    if user is None:
        raise credentials_exception

    return user

async def get_current_active_user(
    current_user: Docente = Depends(get_current_user),
) -> Docente:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: Docente = Depends(get_current_active_user),
) -> Docente:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    return current_user

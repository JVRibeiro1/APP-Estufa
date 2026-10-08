from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ACCESS_TOKEN_MINUTES, JWT_ALGO, JWT_SECRET
from app.database import get_db
from app.models import UsuarioDB

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Instância necessária para registrar a autenticação no Swagger
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expiration}, JWT_SECRET, algorithm=JWT_ALGO
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UsuarioDB:
    token = credentials.credentials.strip()

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user_id = payload.get("sub")
        if not user_id:
            raise PyJWTError("Subject não encontrado")
        user_id_int = int(user_id)
    except (PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(UsuarioDB).where(UsuarioDB.Id == user_id_int))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(current_user: UsuarioDB = Depends(get_current_user)):
    if not current_user.Adm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: Requer privilégios de administrador.",
        )
    return current_user
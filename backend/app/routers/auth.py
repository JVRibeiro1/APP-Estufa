from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import UsuarioDB
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)):
    email_clean = payload.email.lower().strip()
    result = await db.execute(select(UsuarioDB).where(UsuarioDB.Email == email_clean))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    new_user = UsuarioDB(
        Email=email_clean,
        Nome=payload.nome,
        SenhaHash=hash_password(payload.password),
        DataCriacao=datetime.now(timezone.utc),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return TokenOut(
        access_token=create_access_token(new_user.Id),
        user=UserOut.model_validate(new_user),
    )


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    email_clean = payload.email.lower().strip()
    result = await db.execute(select(UsuarioDB).where(UsuarioDB.Email == email_clean))
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.SenhaHash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    return TokenOut(
        access_token=create_access_token(user.Id),
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def me(user: UsuarioDB = Depends(get_current_user)):
    return UserOut.model_validate(user)
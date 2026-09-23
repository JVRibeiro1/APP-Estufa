from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EstufaDB, UsuarioDB, UsuarioEstufaDB
from app.security import hash_password, require_admin

router = APIRouter(prefix="/admin", tags=["Administração"])


# Schemas Pydantic para os Payloads de entrada
class CreateUserSchema(BaseModel):
    email: EmailStr
    nome: str
    senha: str
    adm: bool = False


class CreateEstufaSchema(BaseModel):
    nome_estufa: str


class VinculoEstufaSchema(BaseModel):
    usuario_id: int
    estufa_id: int


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserSchema,
    db: AsyncSession = Depends(get_db),
    admin: UsuarioDB = Depends(require_admin),
):
    result = await db.execute(select(UsuarioDB).where(UsuarioDB.Email == payload.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário cadastrado com este e-mail.",
        )

    # 2. Criar a instância com a senha hashed
    novo_usuario = UsuarioDB(
        Email=payload.email,
        Nome=payload.nome,
        SenhaHash=hash_password(payload.senha),
        Adm=payload.adm,
        DataCriacao=datetime.now(timezone.utc),
    )

    db.add(novo_usuario)
    await db.commit()
    await db.refresh(novo_usuario)

    return {
        "message": "Usuário cadastrado com sucesso!",
        "id": novo_usuario.Id,
        "email": novo_usuario.Email,
    }

@router.post("/estufas", status_code=status.HTTP_201_CREATED)
async def create_estufa(
    payload: CreateEstufaSchema,
    db: AsyncSession = Depends(get_db),
    admin: UsuarioDB = Depends(require_admin),
):
    """Cria uma nova estufa (Apenas Admins)"""
    nova_estufa = EstufaDB(
        NomeEstufa=payload.nome_estufa,
        DataCriacao=datetime.now(timezone.utc),
    )

    db.add(nova_estufa)
    await db.commit()
    await db.refresh(nova_estufa)

    return {
        "message": "Estufa cadastrada com sucesso!",
        "id": nova_estufa.Id,
        "nome_estufa": nova_estufa.NomeEstufa,
    }

@router.post("/vincular-estufa", status_code=status.HTTP_200_OK)
async def vincular_usuario_estufa(
    payload: VinculoEstufaSchema,
    db: AsyncSession = Depends(get_db),
    admin: UsuarioDB = Depends(require_admin),
):
    """Vincula um usuário existente a uma estufa na tabela N:N (Apenas Admins)"""
    query = select(UsuarioEstufaDB).where(
        UsuarioEstufaDB.UsuarioId == payload.usuario_id,
        UsuarioEstufaDB.EstufaId == payload.estufa_id,
    )
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuário já possui acesso a esta estufa.",
        )

    vinculo = UsuarioEstufaDB(
        UsuarioId=payload.usuario_id,
        EstufaId=payload.estufa_id,
        DataVinculo=datetime.now(timezone.utc),
    )

    db.add(vinculo)
    await db.commit()

    return {"message": "Usuário vinculado à estufa com sucesso!"}
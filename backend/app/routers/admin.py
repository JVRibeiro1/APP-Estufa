# app/routers/admin.py

from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import UsuarioDB, UsuarioEstufaDB
from app.security import hash_password, require_admin

router = APIRouter(prefix="/admin", tags=["Administração do Cliente"])


class CreateTeamUserSchema(BaseModel):
    email: EmailStr
    nome: str
    senha: str
    estufa_ids: List[int]  # O Adm seleciona uma ou mais estufas para o novo usuário
    adm: bool = False


@router.post("/team-users", status_code=status.HTTP_201_CREATED)
async def create_team_user(
    payload: CreateTeamUserSchema,
    db: AsyncSession = Depends(get_db),
    admin: UsuarioDB = Depends(require_admin),
):
    """
    O Adm do Cliente cria um usuário vinculando-o às estufas selecionadas.
    O backend valida se todas as estufas pertencem ao Adm logado.
    """
    if not payload.estufa_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selecione pelo menos uma estufa para o novo usuário.",
        )

    # 1. Buscar estufas que o Administrador logado realmente tem acesso
    stmt_estufas_adm = select(UsuarioEstufaDB.EstufaId).where(
        UsuarioEstufaDB.UsuarioId == admin.Id
    )
    res_estufas_adm = await db.execute(stmt_estufas_adm)
    estufas_permitidas = set(res_estufas_adm.scalars().all())

    # Se for um Super Admin do sistema que não tem vinculo na N:N, podemos permitir todas
    if not estufas_permitidas and admin.Adm:
        from app.models import EstufaDB
        res_todas = await db.execute(select(EstufaDB.Id))
        estufas_permitidas = set(res_todas.scalars().all())

    # Validate: garante que o Adm não tente vincular uma estufa de outro cliente
    for e_id in payload.estufa_ids:
        if e_id not in estufas_permitidas:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Você não possui permissão para gerenciar a estufa com ID {e_id}.",
            )

    # 2. Verificar se o e-mail já existe
    stmt_user = select(UsuarioDB).where(UsuarioDB.Email == payload.email)
    res_user = await db.execute(stmt_user)
    if res_user.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário cadastrado com este e-mail.",
        )

    # 3. Criar o novo usuário
    novo_usuario = UsuarioDB(
        Email=payload.email,
        Nome=payload.nome,
        SenhaHash=hash_password(payload.senha),
        Adm=payload.adm,
        DataCriacao=datetime.now(timezone.utc),
    )
    db.add(novo_usuario)
    await db.flush()  # Obtém o Id do novo_usuario

    # 4. Vincular às estufas selecionadas
    for e_id in payload.estufa_ids:
        vinculo = UsuarioEstufaDB(
            UsuarioId=novo_usuario.Id,
            EstufaId=e_id,
            DataVinculo=datetime.now(timezone.utc),
        )
        db.add(vinculo)

    await db.commit()
    await db.refresh(novo_usuario)

    return {
        "message": "Usuário criado e vinculado com sucesso!",
        "usuario_id": novo_usuario.Id,
        "email": novo_usuario.Email,
        "estufas_vinculadas": payload.estufa_ids,
    }
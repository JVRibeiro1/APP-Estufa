# app/routers/estufa.py

from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EstufaDB, UsuarioEstufaDB, UsuarioDB
from app.security import get_current_user

router = APIRouter(prefix="/estufas", tags=["Estufas"])


class EstufaOut(BaseModel):
    Id: int
    NomeEstufa: str

    class Config:
        from_attributes = True


@router.get("/my-estufas", response_model=List[EstufaOut])
async def get_my_estufas(
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Retorna a lista de todas as estufas vinculadas ao usuário atual"""
    
    # Se for Administrador, traz todas as estufas do sistema
    if current_user.Adm:
        query = select(EstufaDB)
    else:
        # Se for usuário comum, traz apenas as estufas vinculadas na tabela N:N
        query = (
            select(EstufaDB)
            .join(UsuarioEstufaDB, EstufaDB.Id == UsuarioEstufaDB.EstufaId)
            .where(UsuarioEstufaDB.UsuarioId == current_user.Id)
        )

    result = await db.execute(query)
    estufas = result.scalars().all()

    return estufas
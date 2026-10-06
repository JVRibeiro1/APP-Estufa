from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import SensorReadingDB, UsuarioDB
from app.schemas import SensorReadingOut
from app.security import get_current_user

router = APIRouter(prefix="/sensors", tags=["Sensores"])

@router.get("/latest", response_model=Optional[SensorReadingOut])
async def get_latest_sensor_reading(
    estufa_id: int = Query(..., description="ID da estufa para filtrar os sensores"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Retorna a leitura mais recente de uma estufa específica"""
    query = (
        select(SensorReadingDB)
        .where(SensorReadingDB.IdEstufa == estufa_id)
        .order_by(SensorReadingDB.DataHoraGravacao.desc())
    )
    result = await db.execute(query)
    reading = result.scalars().first()

    # Em vez de disparar 404, retorna None/null com HTTP 200
    return reading


@router.get("/history", response_model=List[SensorReadingOut])
async def get_sensor_history(
    estufa_id: int = Query(..., description="ID da estufa para filtrar o histórico"),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Retorna o histórico de leituras de uma estufa específica"""
    query = (
        select(SensorReadingDB)
        .where(SensorReadingDB.IdEstufa == estufa_id)
        .order_by(SensorReadingDB.DataHoraGravacao  .desc())
        .limit(limit)
    )
    result = await db.execute(query)
    readings = result.scalars().all()

    return readings
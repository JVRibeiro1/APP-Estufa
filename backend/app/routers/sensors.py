from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SensorReadingDB
from app.schemas import SensorReadingOut
from app.security import get_current_user

from datetime import datetime
from typing import List, Optional


router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.get("/latest", response_model=Optional[SensorReadingOut])
async def latest_sensor(
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    result = await db.execute(
        select(SensorReadingDB)
        .order_by(desc(SensorReadingDB.DataHoraEnvio))
        .limit(1)
    )
    reading = result.scalars().first()
    if not reading:
        return None
    return SensorReadingOut.model_validate(reading)

@router.get("/history", response_model=List[SensorReadingOut])
async def sensor_history(
    data_inicio: datetime = Query(..., description="Data/Hora inicial no formato ISO (Ex: 2026-09-01T00:00:00)"),
    data_fim: datetime = Query(..., description="Data/Hora final no formato ISO (Ex: 2026-09-17T23:59:59)"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if data_inicio > data_fim:
        raise HTTPException(
            status_code=400, detail="A data_inicio não pode ser posterior à data_fim"
        )

    query = (
        select(SensorReadingDB)
        .where(
            SensorReadingDB.DataHoraEnvio >= data_inicio,
            SensorReadingDB.DataHoraEnvio <= data_fim,
        )
        .order_by(desc(SensorReadingDB.DataHoraEnvio))
    )

    result = await db.execute(query)
    readings = result.scalars().all()

    return [SensorReadingOut.model_validate(r) for r in readings]
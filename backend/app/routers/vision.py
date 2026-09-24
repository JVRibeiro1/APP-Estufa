from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import DeteccaoInferenciaDB, UsuarioDB, UsuarioEstufaDB
from app.security import get_current_user
from app.services.push import send_expo_push_notification

router = APIRouter(prefix="/vision", tags=["Visão Computacional & Alertas"])


# Schema para recepção dos dados da IA/Inspecção
class DetectionIn(BaseModel):
    estufa_id: int
    classe: str  # ex: 'bacteriano', 'fungico', 'saudavel'
    confianca: float
    imagem_blob: Optional[str] = None
    prob_bacteriano: Optional[float] = 0.0
    prob_fungico: Optional[float] = 0.0
    prob_saudavel: Optional[float] = 0.0
    patogeno_detectado: bool = False
    alerta: bool = False
    modelo_versao: Optional[str] = "yolo11n_cls_alface.pt"
    tempo_inferencia_ms: Optional[float] = 0.0


# --- FUNÇÃO AUXILIAR DE DISPARO DE PUSH ---
async def notify_greenhouse_users(
    estufa_id: int, classe: str, confianca: float, db: AsyncSession
):
    """Busca os push tokens dos usuários da estufa e dispara a notificação nativa no celular"""
    try:
        stmt = (
            select(UsuarioDB.PushToken)
            .join(UsuarioEstufaDB, UsuarioDB.Id == UsuarioEstufaDB.UsuarioId)
            .where(
                UsuarioEstufaDB.EstufaId == estufa_id,
                UsuarioDB.PushToken.isnot(None),
                UsuarioDB.PushToken != "",
            )
        )
        result = await db.execute(stmt)
        tokens = [t for t in result.scalars().all() if t]

        if tokens:
            conf_percent = int(confianca * 100) if confianca <= 1 else int(confianca)
            await send_expo_push_notification(
                tokens=tokens,
                title="⚠️ Alerta de Fitossanidade!",
                body=f"Detecção de {classe.upper()} ({conf_percent}%) na sua estufa.",
                data={"estufa_id": estufa_id},
            )
        else:
            print(f"Nenhum PushToken encontrado para usuários vinculados à Estufa {estufa_id}.")
    except Exception as e:
        print(f"Erro ao processar notificação push para a Estufa {estufa_id}: {e}")


# --- ENDPOINTS EXISTENTES (CONSULTA NO APP) ---

@router.get("/alerts")
async def get_alerts_by_estufa(
    estufa_id: int = Query(..., description="ID da estufa para listar os alertas"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Retorna os alertas e detecções de doenças filtrados por estufa"""
    
    query = (
        select(DeteccaoInferenciaDB)
        .where(
            DeteccaoInferenciaDB.EstufaId == estufa_id,
            DeteccaoInferenciaDB.Alerta == True
        )
        .order_by(DeteccaoInferenciaDB.DataHoraDeteccao.desc())
    )
    
    result = await db.execute(query)
    detections = result.scalars().all()

    alerts = []
    for d in detections:
        created_at_str = (
            d.DataHoraDeteccao.isoformat()
            if d.DataHoraDeteccao
            else datetime.now(timezone.utc).isoformat()
        )
        alerts.append({
            "id": str(d.Id),
            "estufa_id": d.EstufaId,
            "disease": d.Classe,
            "confidence": float(d.Confianca) if d.Confianca is not None else 0.0,
            "severity": "error" if d.PatogenoDetectado else "warning",
            "plant_zone": f"Zona {d.EstufaId}",
            "image_url": d.ImagemBlob,
            "created_at": created_at_str,
            "read": False,
            "resolved": False
        })

    return alerts


@router.get("/alerts/unread-count")
async def get_unread_count(
    estufa_id: int = Query(..., description="ID da estufa para contagem de alertas"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Retorna o número de alertas pendentes para a estufa selecionada"""
    query = (
        select(func.count(DeteccaoInferenciaDB.Id))
        .where(
            DeteccaoInferenciaDB.EstufaId == estufa_id,
            DeteccaoInferenciaDB.Alerta == True
        )
    )
    result = await db.execute(query)
    count = result.scalar() or 0

    return {"count": count}


# --- ENDPOINT: RECEBE INFERÊNCIA DA IA & DISPARA O PUSH ---

@router.post("/detect", status_code=status.HTTP_201_CREATED)
async def receive_detection(
    payload: DetectionIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint chamado pela API/Script do YOLO11.
    Salva a detecção no banco de dados e, se houver alerta (Alerta=True),
    envia automaticamente o Push Notification para os celulares dos produtores.
    """
    now = datetime.now(timezone.utc)
    
    nova_deteccao = DeteccaoInferenciaDB(
        EstufaId=payload.estufa_id,
        ImagemBlob=payload.imagem_blob,
        Classe=payload.classe,
        Confianca=payload.confianca,
        ProbBacteriano=payload.prob_bacteriano,
        ProbFungico=payload.prob_fungico,
        ProbSaudavel=payload.prob_saudavel,
        PatogenoDetectado=payload.patogeno_detectado,
        Alerta=payload.alerta,
        ModeloVersao=payload.modelo_versao,
        TempoInferenciaMs=payload.tempo_inferencia_ms,
        DataHoraDeteccao=now,
        DataHoraGravacao=now,
    )

    db.add(nova_deteccao)
    await db.commit()
    await db.refresh(nova_deteccao)

    # Se for um alerta/doença, dispara a notificação no celular
    if payload.alerta:
        await notify_greenhouse_users(
            estufa_id=payload.estufa_id,
            classe=payload.classe,
            confianca=payload.confianca,
            db=db,
        )

    return {
        "message": "Detecção gravada com sucesso",
        "id": nova_deteccao.Id,
        "push_sent": payload.alerta,
    }
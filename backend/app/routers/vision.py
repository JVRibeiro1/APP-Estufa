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
from app.services.azure_blob import build_image_url

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
    prob_alface: Optional[float] = None
    modelo_dominio_versao: Optional[str] = None
    tempo_verificacao_ms: Optional[float] = 0.0


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
    unread_only: bool = Query(False, description="Filtrar apenas alertas não lidos"),
    unresolved_only: bool = Query(False, description="Filtrar apenas alertas não resolvidos"),
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
    )

    # Se pedir apenas não lidos
    if unread_only:
        query = query.where(
            (DeteccaoInferenciaDB.Lido == False) | (DeteccaoInferenciaDB.Lido.is_(None))
        )

    # Se pedir apenas não resolvidos (para o Dashboard)
    if unresolved_only:
        query = query.where(
            (DeteccaoInferenciaDB.Resolvido == False) | (DeteccaoInferenciaDB.Resolvido.is_(None))
        )
    
    query = query.order_by(DeteccaoInferenciaDB.DataHoraDeteccao.desc())
    
    result = await db.execute(query)
    detections = result.scalars().all()

    alerts = []
    for d in detections:
        created_at_str = (
            d.DataHoraDeteccao.isoformat()
            if d.DataHoraDeteccao
            else datetime.now(timezone.utc).isoformat()
        )
        
        # Mapeamento explícito lidando com valores NULL/None do SQL Server
        is_read = bool(d.Lido) if d.Lido is not None else False
        is_resolved = bool(d.Resolvido) if d.Resolvido is not None else False

        alerts.append({
            "id": str(d.Id),
            "estufa_id": d.EstufaId,
            "disease": d.Classe,
            "confidence": float(d.Confianca) if d.Confianca is not None else 0.0,
            "severity": "error" if d.PatogenoDetectado else "warning",
            "plant_zone": f"Zona {d.EstufaId}",
            "image_url": build_image_url(d.ImagemBlob),  
            "image_base64": None,
            "created_at": created_at_str,
            "read": is_read,
            "resolved": is_resolved
        })

    return alerts


@router.get("/alerts/unread-count")
async def get_unread_count(
    estufa_id: int = Query(..., description="ID da estufa para contagem de alertas"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Retorna o número de alertas NÃO LIDOS para a estufa (atualiza o badge do Dashboard)"""
    query = (
        select(func.count(DeteccaoInferenciaDB.Id))
        .where(
            DeteccaoInferenciaDB.EstufaId == estufa_id,
            DeteccaoInferenciaDB.Alerta == True,
            (DeteccaoInferenciaDB.Lido == False) | (DeteccaoInferenciaDB.Lido.is_(None))
        )
    )
    result = await db.execute(query)
    count = result.scalar() or 0

    return {"count": count}


# --- NOVOS ENDPOINTS: DETALHE, MARCAR LIDO E RESOLVER ---

@router.get("/alerts/{alert_id}")
async def get_alert_detail(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Retorna o detalhe de um alerta específico pelo ID e marca como lido"""
    query = select(DeteccaoInferenciaDB).where(DeteccaoInferenciaDB.Id == alert_id)
    result = await db.execute(query)
    d = result.scalar_one_or_none()

    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado")

    # Marca como lido ao visualizar os detalhes
    if hasattr(d, "Lido") and not d.Lido:
        d.Lido = True
        await db.commit()

    created_at_str = (
        d.DataHoraDeteccao.isoformat()
        if d.DataHoraDeteccao
        else datetime.now(timezone.utc).isoformat()
    )

    return {
        "id": str(d.Id),
        "estufa_id": d.EstufaId,
        "disease": d.Classe,
        "confidence": float(d.Confianca) if d.Confianca is not None else 0.0,
        "severity": "error" if d.PatogenoDetectado else "warning",
        "plant_zone": f"Zona {d.EstufaId}",
        "image_url": build_image_url(d.ImagemBlob),  # <--- URL completa montada aqui
        "image_base64": None,
        "description": f"Foi identificada a classe '{d.Classe}' com probabilidade bacteriana de {int((d.ProbBacteriano or 0)*100)}% e fúngica de {int((d.ProbFungico or 0)*100)}%.",
        "recommendations": [
            "Inspecione visualmente a área afetada na estufa.",
            "Isole o lote caso haja avanço dos sintomas de patógeno.",
            "Verifique os parâmetros de umidade e temperatura nos sensores."
        ],
        "created_at": created_at_str,
        "read": bool(getattr(d, "Lido", True)),
        "resolved": bool(getattr(d, "Resolvido", False))    
    }


@router.patch("/alerts/{alert_id}/read")
async def mark_alert_as_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Marca o alerta como lido/visualizado no banco de dados"""
    query = select(DeteccaoInferenciaDB).where(DeteccaoInferenciaDB.Id == alert_id)
    result = await db.execute(query)
    d = result.scalar_one_or_none()

    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado")

    if hasattr(d, "Lido"):
        d.Lido = True
        await db.commit()

    return {"message": "Alerta marcado como lido", "id": alert_id}


@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioDB = Depends(get_current_user),
):
    """Marca o alerta como resolvido e lido no banco de dados"""
    query = select(DeteccaoInferenciaDB).where(DeteccaoInferenciaDB.Id == alert_id)
    result = await db.execute(query)
    d = result.scalar_one_or_none()

    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado")

    if hasattr(d, "Resolvido"):
        d.Resolvido = True
    if hasattr(d, "Lido"):
        d.Lido = True

    await db.commit()

    created_at_str = (
        d.DataHoraDeteccao.isoformat()
        if d.DataHoraDeteccao
        else datetime.now(timezone.utc).isoformat()
    )

    return {
        "id": str(d.Id),
        "estufa_id": d.EstufaId,
        "disease": d.Classe,
        "confidence": float(d.Confianca) if d.Confianca is not None else 0.0,
        "severity": "error" if d.PatogenoDetectado else "warning",
        "plant_zone": f"Zona {d.EstufaId}",
        "image_url": build_image_url(d.ImagemBlob),  
        "image_base64": None,
        "created_at": created_at_str,
        "read": True,
        "resolved": True
    }


# --- ENDPOINT: RECEBE INFERÊNCIA DA IA & DISPARA O PUSH ---

@router.post("/detect", status_code=status.HTTP_200_OK)
async def receive_detection(
    payload: DetectionIn,
    db: AsyncSession = Depends(get_db),
):
    push_sent = False

    # Apenas dispara o push se a flag de alerta estiver True
    if payload.alerta:
        await notify_greenhouse_users(
            estufa_id=payload.estufa_id,
            classe=payload.classe,
            confianca=payload.confianca,
            db=db,
        )
        push_sent = True

    return {
        "message": "Detecção processada com sucesso (sem gravação na base de dados)",
        "push_sent": push_sent,
    }
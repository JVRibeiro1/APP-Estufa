from datetime import datetime
from typing import List, Optional
import httpx
from fastapi import APIRouter, Depends
from app.schemas import InferencePayload, DetectionResponse
from app.models import UsuarioDB
from app.security import get_current_user

router = APIRouter(prefix="/vision", tags=["Visão Computacional"])

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_expo_push_notification(expo_push_token: str, title: str, body: str, data: Optional[dict] = None):
    """Envia a notificação push nativa para o servidor da Expo."""
    payload = {
        "to": expo_push_token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data or {},
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(EXPO_PUSH_URL, json=payload)
        except Exception as e:
            print(f"Erro ao enviar push notification: {e}")


@router.post("/process-status", response_model=DetectionResponse)
async def process_plant_status(payload: InferencePayload):
    is_unhealthy = payload.patogeno_detectado or payload.alerta or payload.classe.lower() != "saudavel"
    
    if is_unhealthy:
        mensagem = (
            f"ALERTA: Anomalia ({payload.classe_exibicao}) detectada com {round(payload.confianca * 100, 1)}% de confiança!"
        )
        
        # Cole aqui o ExponentPushToken gerado no console do seu celular
        user_push_token = "ExponentPushToken[N8KzbfEg8ySha4uResP-Fw]"

        if user_push_token and user_push_token.startswith("ExponentPushToken"):
            await send_expo_push_notification(
                expo_push_token=user_push_token,
                title="🚨 Alerta na Estufa!",
                body=f"Detectado: {payload.classe_exibicao} ({round(payload.confianca * 100, 1)}%)",
                data={"screen": "alerts"}
            )
    else:
        mensagem = "Planta analisada e classificada como saudável."

    return {
        "id": 0,
        "alerta_gerado": is_unhealthy,
        "mensagem": mensagem
    }


@router.get("/alerts")
async def get_alerts(unread_only: bool = False, current_user: UsuarioDB = Depends(get_current_user)):
    """Retorna os alertas para a lista no app"""
    return []


@router.get("/alerts/unread-count")
async def get_unread_count(current_user: UsuarioDB = Depends(get_current_user)):
    """Retorna a contagem de alertas não lidos"""
    return {"count": 0}
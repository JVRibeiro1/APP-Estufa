from typing import Any, Dict, List, Optional
import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_expo_push_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
):
    """Envia notificação nativa para os tokens fornecidos via Expo Push API"""
    # Remove duplicados e filtra apenas tokens válidos do Expo
    valid_tokens = list(
        {t for t in tokens if t and isinstance(t, str) and t.startswith("ExponentPushToken")}
    )

    if not valid_tokens:
        print("⚠️ Nenhum PushToken válido encontrado para envio.")
        return

    # Payload completo com parâmetros de prioridade e canal do Android
    messages = [
        {
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "channelId": "default",  # Obrigatório para exibir o banner no Android 8+
            "priority": "high",       # Força a entrega imediata acendendo a tela/vibrando
            "badge": 1,
            "data": data or {},
        }
        for token in valid_tokens
    ]

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(EXPO_PUSH_URL, json=messages, headers=headers)
            res_json = response.json()
            print(f"📡 Resposta da Expo Push API [{response.status_code}]: {res_json}")
        except Exception as e:
            print(f"❌ Erro ao disparar requisição push para Expo: {e}")
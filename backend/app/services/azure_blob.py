import os

AZURE_CONTAINER_URL = os.getenv(
    "AZURE_CONTAINER_URL",
    "https://tccimagens.blob.core.windows.net/imagens-alface"
)

def build_image_url(image_blob_path: str | None) -> str | None:
    """
    Converte o caminho relativo do blob (ex: 'estufa-01/2026/09/...')
    em uma URL pública completa para exibição no App e Web.
    """
    if not image_blob_path:
        return None
    
    # Se já for uma URL completa ou imagem base64, mantém original
    if image_blob_path.startswith(("http://", "https://", "data:image")):
        return image_blob_path
        
    blob_path = image_blob_path.lstrip('/')
    return f"{AZURE_CONTAINER_URL}/{blob_path}"
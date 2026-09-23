from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    nome: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    Email: EmailStr
    Nome: Optional[str] = None
    Adm: bool = False


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SensorReadingIn(BaseModel):
    device_id: str
    temperatura: float
    umidade: float
    luminosidade: Optional[int] = None
    temp_teto: Optional[float] = None
    umid_teto: Optional[float] = None


class SensorReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    DeviceId: str
    Temperatura: Optional[float]
    Umidade: Optional[float]
    Luminosidade: Optional[int]
    DataHoraEnvio: datetime


# --- Novos Schemas para Visão Computacional / IA ---

class ProbabilidadesSchema(BaseModel):
    bacteriano: float
    fungico: float
    saudavel: float


class InferencePayload(BaseModel):
    classe: str
    classe_exibicao: str
    confianca: float
    probabilidades: ProbabilidadesSchema
    patogeno_detectado: bool
    alerta: bool
    tempo_inferencia_ms: float
    detectado_em: datetime
    modelo_versao: str
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_w: Optional[float] = None
    bbox_h: Optional[float] = None
    heatmap_base64: Optional[str] = None
    imagem_blob: Optional[str] = None
    estufa_id: Optional[int] = 1


class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alerta_gerado: bool
    mensagem: str

class UsuarioResponse(BaseModel):
    id: int
    email: str
    nome: Optional[str] = None
    adm: bool

    class Config:
        from_attributes = True
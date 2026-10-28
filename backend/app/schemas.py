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
    IdEstufa: int
    DeviceId: str
    Temperatura: Optional[float] = None
    Umidade: Optional[float] = None
    Luminosidade: Optional[int] = None
    DataHoraEnvio: datetime
    DataHoraGravacao: datetime
    TempTeto: Optional[float] = None
    UmidTeto: Optional[float] = None


class ProbabilidadesSchema(BaseModel):
    bacteriano: float
    fungico: float
    saudavel: float


class InferencePayload(BaseModel):
    estufa_id: Optional[int] = 1
    classe: str
    confianca: float
    imagem_blob: Optional[str] = None
    prob_bacteriano: Optional[float] = None
    prob_fungico: Optional[float] = None
    prob_saudavel: Optional[float] = None
    patogeno_detectado: bool
    alerta: bool
    modelo_versao: str
    tempo_inferencia_ms: float

    prob_alface: Optional[float] = None
    modelo_dominio_versao: Optional[str] = None
    tempo_verificacao_ms: Optional[float] = None

    classe_exibicao: Optional[str] = None
    probabilidades: Optional[ProbabilidadesSchema] = None
    detectado_em: Optional[datetime] = None


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
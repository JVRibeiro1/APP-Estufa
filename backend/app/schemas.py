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
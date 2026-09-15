from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
import os
import logging
import urllib.parse

# SQLAlchemy Imports
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Numeric, Text, select, desc

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ---------- Configuração do SQL Server Local ----------
SERVER = os.environ.get("DB_SERVER", "localhost\\SQLEXPRESS")
DATABASE = os.environ.get("DB_NAME", "app_homolog")
DRIVER = "ODBC Driver 18 for SQL Server"

odbc_str = f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;TrustServerCertificate=yes;"
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    f"mssql+aioodbc:///?odbc_connect={urllib.parse.quote_plus(odbc_str)}"
)

JWT_SECRET = os.environ.get("JWT_SECRET", "alface-ai-dev-secret-change-me")
JWT_ALGO = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 24 * 7  # 7 dias

# Configuração do Engine SQL Server
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AlfaceAI Greenhouse API - SQL Server Version")
api = APIRouter(prefix="/api")

# Password hashing
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- Tabelas SQL (ORM) ----------
class UsuarioDB(Base):
    __tablename__ = "Usuarios"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    Email = Column(String(255), unique=True, index=True, nullable=False)
    Nome = Column(String(255), nullable=True)
    SenhaHash = Column(String(255), nullable=False)
    DataCriacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SensorReadingDB(Base):
    __tablename__ = "LeiturasSensores"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    DeviceId = Column(String(50), nullable=False)
    Temperatura = Column(Numeric(5, 2), nullable=True)
    Umidade = Column(Numeric(5, 2), nullable=True)
    Luminosidade = Column(Integer, nullable=True)
    DataHoraEnvio = Column(DateTime, nullable=False, index=True)
    DataHoraGravacao = Column(DateTime, nullable=True)
    TempTeto = Column(Numeric(5, 2), nullable=True)
    UmidTeto = Column(Numeric(5, 2), nullable=True)

class DeteccaoInferenciaDB(Base):
    __tablename__ = "Deteccoes"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    EstufaId = Column(Integer, nullable=True)
    ImagemBlob = Column(String(400), nullable=False)
    Classe = Column(String(20), nullable=False)
    Confianca = Column(Numeric(7, 6), nullable=False)
    ProbBacteriano = Column(Numeric(7, 6), nullable=False)
    ProbFungico = Column(Numeric(7, 6), nullable=False)
    ProbSaudavel = Column(Numeric(7, 6), nullable=False)
    PatogenoDetectado = Column(Boolean, nullable=False, default=False)
    Alerta = Column(Boolean, nullable=False, default=False)
    ModeloVersao = Column(String(100), nullable=False)
    TempoInferenciaMs = Column(Numeric(9, 3), nullable=False)
    DataHoraDeteccao = Column(DateTime, nullable=False, index=True)
    DataHoraGravacao = Column(DateTime, nullable=False)
    BboxX = Column(Float, nullable=True)
    BboxY = Column(Float, nullable=True)
    BboxW = Column(Float, nullable=True)
    BboxH = Column(Float, nullable=True)
    HeatmapBlob = Column(String(400), nullable=True)


# ---------- Pydantic Models ----------
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


# ---------- Helpers & Middlewares ----------
def hash_password(p: str) -> str:
    return pwd.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd.verify(p, h)

def create_access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, JWT_SECRET, algorithm=JWT_ALGO)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    # Remove espaços em branco extras nas pontas
    auth_clean = authorization.strip()

    if not auth_clean.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    # Extrai o token ignorando múltiplos espaços inter/api/auth/memediários
    token = auth_clean.split(" ", 1)[1].strip()
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError()
        user_id_int = int(user_id)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    result = await db.execute(select(UsuarioDB).where(UsuarioDB.Id == user_id_int))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


# ---------- Auth Routes ----------
@api.post("/auth/register", response_model=TokenOut, status_code=201)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)):
    email_clean = payload.email.lower().strip()
    result = await db.execute(select(UsuarioDB).where(UsuarioDB.Email == email_clean))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    
    novo_usuario = UsuarioDB(
        Email=email_clean,
        Nome=payload.nome,
        SenhaHash=hash_password(payload.password),
        DataCriacao=datetime.now(timezone.utc)
    )
    db.add(novo_usuario)
    await db.commit()
    await db.refresh(novo_usuario)
    
    token = create_access_token(novo_usuario.Id)
    return TokenOut(access_token=token, user=UserOut.model_validate(novo_usuario))


@api.post("/auth/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    email_clean = payload.email.lower().strip()
    result = await db.execute(select(UsuarioDB).where(UsuarioDB.Email == email_clean))
    usuario = result.scalars().first()
    
    if not usuario or not verify_password(payload.password, usuario.SenhaHash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
    token = create_access_token(usuario.Id)
    return TokenOut(access_token=token, user=UserOut.model_validate(usuario))


@api.get("/auth/me", response_model=UserOut)
async def me(user: UsuarioDB = Depends(get_current_user)):
    return UserOut.model_validate(user)


# ---------- Sensor Routes ----------
@api.get("/sensors/latest", response_model=Optional[SensorReadingOut])
async def latest_sensor(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(SensorReadingDB).order_by(desc(SensorReadingDB.DataHoraEnvio)).limit(1))
    doc = result.scalars().first()
    if not doc:
        return None
    return SensorReadingOut.model_validate(doc)


@api.post("/sensors/data", response_model=SensorReadingOut, status_code=201)
async def push_sensor_data(payload: SensorReadingIn, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    new_reading = SensorReadingDB(
        DeviceId=payload.device_id,
        Temperatura=payload.temperatura,
        Umidade=payload.umidade,
        Luminosidade=payload.luminosidade,
        TempTeto=payload.temp_teto,
        UmidTeto=payload.umid_teto,
        DataHoraEnvio=now,
        DataHoraGravacao=now
    )
    db.add(new_reading)
    await db.commit()
    await db.refresh(new_reading)
    return SensorReadingOut.model_validate(new_reading)


# ---------- Health ----------
@api.get("/")
async def root():
    return {"status": "ok", "service": "AlfaceAI Greenhouse API - SQL Server"}

app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
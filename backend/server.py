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
import uuid
import random
import logging

# SQLAlchemy Imports
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON, select, desc

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Configuração
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./estufa.db")
JWT_SECRET = os.environ.get("JWT_SECRET", "alface-ai-dev-secret-change-me")
JWT_ALGO = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 24 * 7  # 7 days

# Configuração do Banco Relacional (SQLite Assíncrono)
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AlfaceAI Greenhouse API - SQL Version")
api = APIRouter(prefix="/api")

# Password hashing
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- Tabelas SQL (ORM) ----------
class UserDB(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime)

class SensorReadingDB(Base):
    __tablename__ = "sensor_readings"
    id = Column(String, primary_key=True, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    soil_moisture = Column(Float)
    light = Column(Float)
    co2 = Column(Float)
    timestamp = Column(DateTime, index=True)

class AlertDB(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, index=True)
    disease = Column(String)
    confidence = Column(Float)
    severity = Column(String, default="warning")
    plant_zone = Column(String, nullable=True)
    description = Column(String, nullable=True)
    recommendations = Column(JSON, nullable=True)
    image_base64 = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    read = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, index=True)


# ---------- Pydantic Models (Validação) ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    name: Optional[str] = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class SensorReadingIn(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: float
    light: float
    co2: float

class SensorReadingOut(SensorReadingIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    timestamp: datetime

class AlertIn(BaseModel):
    disease: str
    confidence: float
    severity: str = "warning"
    plant_zone: Optional[str] = None
    description: Optional[str] = None
    recommendations: Optional[List[str]] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None

class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    disease: str
    confidence: float
    severity: str
    plant_zone: Optional[str] = None
    description: Optional[str] = None
    recommendations: Optional[List[str]] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    read: bool
    resolved: bool
    created_at: datetime


# ---------- Helpers & Middlewares ----------
def hash_password(p: str) -> str:
    return pwd.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd.verify(p, h)

def create_access_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET, algorithm=JWT_ALGO)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


# ---------- Startup / Seed Dados ----------
@app.on_event("startup")
async def startup():
    # Cria o arquivo SQLite e as tabelas fisicamente
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Seed demo user
        demo_email = "demo@estufa.com"
        result = await session.execute(select(UserDB).where(UserDB.email == demo_email))
        if not result.scalars().first():
            demo_user = UserDB(
                id=uuid.uuid4().hex,
                email=demo_email,
                name="Produtor Demo",
                password_hash=hash_password("demo1234"),
                created_at=datetime.now(timezone.utc)
            )
            session.add(demo_user)
            await session.commit()
            logger.info("Seeded demo user: demo@estufa.com / demo1234")

        # Seed sensor readings
        result = await session.execute(select(SensorReadingDB))
        if not result.scalars().first():
            now = datetime.now(timezone.utc)
            for i in range(24):
                reading = SensorReadingDB(
                    id=uuid.uuid4().hex,
                    temperature=round(22 + random.uniform(-2, 3), 1),
                    humidity=round(65 + random.uniform(-5, 10), 1),
                    soil_moisture=round(58 + random.uniform(-8, 8), 1),
                    light=round(720 + random.uniform(-100, 200), 0),
                    co2=round(420 + random.uniform(-20, 60), 0),
                    timestamp=now - timedelta(hours=23 - i)
                )
                session.add(reading)
            await session.commit()
            logger.info("Seeded 24 sensor readings")

        # Seed demo alerts
        result = await session.execute(select(AlertDB))
        if not result.scalars().first():
            alert = AlertDB(
                id=uuid.uuid4().hex,
                disease="Míldio (Downy Mildew)",
                confidence=0.92,
                severity="error",
                plant_zone="Bancada A - Fileira 3",
                description="Manchas amareladas na face superior das folhas com mofo cinza-esbranquiçado na face inferior.",
                recommendations=[
                    "Reduzir a umidade relativa abaixo de 70%",
                    "Aumentar a ventilação da estufa"
                ],
                image_url="https://images.pexels.com/photos/3016319/pexels-photo-3016319.jpeg",
                read=False,
                resolved=False,
                created_at=datetime.now(timezone.utc) - timedelta(hours=2)
            )
            session.add(alert)
            await session.commit()
            logger.info("Seeded demo alerts")


# ---------- Auth Routes ----------
@api.post("/auth/register", response_model=TokenOut)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower()
    result = await db.execute(select(UserDB).where(UserDB.email == email))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    
    new_user = UserDB(
        id=uuid.uuid4().hex,
        email=email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    token = create_access_token(new_user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(new_user))


@api.post("/auth/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.email == payload.email.lower()))
    user = result.scalars().first()
    
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@api.get("/auth/me", response_model=UserOut)
async def me(user: UserDB = Depends(get_current_user)):
    return UserOut.model_validate(user)


# ---------- Sensor Routes ----------
@api.get("/sensors/latest", response_model=Optional[SensorReadingOut])
async def latest_sensor(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(SensorReadingDB).order_by(desc(SensorReadingDB.timestamp)).limit(1))
    doc = result.scalars().first()
    if not doc:
        return None
    return SensorReadingOut.model_validate(doc)


@api.get("/sensors/history", response_model=List[SensorReadingOut])
async def sensor_history(limit: int = 24, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(SensorReadingDB).order_by(desc(SensorReadingDB.timestamp)).limit(limit))
    docs = result.scalars().all()
    # Inverte para ordem cronológica (mais antigo primeiro na renderização dos gráficos)
    return [SensorReadingOut.model_validate(d) for d in reversed(docs)]


@api.post("/sensors/data", response_model=SensorReadingOut)
async def push_sensor_data(payload: SensorReadingIn, db: AsyncSession = Depends(get_db)):
    """Endpoint público para o gateway IoT enviar leituras."""
    new_reading = SensorReadingDB(
        id=uuid.uuid4().hex,
        temperature=payload.temperature,
        humidity=payload.humidity,
        soil_moisture=payload.soil_moisture,
        light=payload.light,
        co2=payload.co2,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(new_reading)
    await db.commit()
    await db.refresh(new_reading)
    return SensorReadingOut.model_validate(new_reading)


# ---------- Alerts Routes ----------
@api.get("/alerts", response_model=List[AlertOut])
async def list_alerts(unread_only: bool = False, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    query = select(AlertDB).order_by(desc(AlertDB.created_at)).limit(100)
    if unread_only:
        query = query.where(AlertDB.read == False)
        
    result = await db.execute(query)
    docs = result.scalars().all()
    return [AlertOut.model_validate(d) for d in docs]


@api.get("/alerts/unread-count")
async def unread_count(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(AlertDB).where(AlertDB.read == False))
    count = len(result.scalars().all())
    return {"count": count}


@api.get("/alerts/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(AlertDB).where(AlertDB.id == alert_id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
        
    if not doc.read:
        doc.read = True
        await db.commit()
        await db.refresh(doc)
        
    return AlertOut.model_validate(doc)


@api.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(alert_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(AlertDB).where(AlertDB.id == alert_id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
        
    doc.resolved = True
    doc.read = True
    await db.commit()
    await db.refresh(doc)
    
    return AlertOut.model_validate(doc)


@api.post("/alerts/webhook", response_model=AlertOut)
async def alert_webhook(payload: AlertIn, db: AsyncSession = Depends(get_db)):
    """Webhook público para a API de visão computacional."""
    new_alert = AlertDB(
        id=uuid.uuid4().hex,
        disease=payload.disease,
        confidence=payload.confidence,
        severity=payload.severity,
        plant_zone=payload.plant_zone,
        description=payload.description,
        recommendations=payload.recommendations,
        image_base64=payload.image_base64,
        image_url=payload.image_url,
        read=False,
        resolved=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)
    return AlertOut.model_validate(new_alert)


# ---------- Health ----------
@api.get("/")
async def root():
    return {"status": "ok", "service": "AlfaceAI Greenhouse API - SQL"}

app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
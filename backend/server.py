from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
import os
import uuid
import random
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Config
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ.get("JWT_SECRET", "alface-ai-dev-secret-change-me")
JWT_ALGO = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 24 * 7  # 7 days

# DB
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Password hashing
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AlfaceAI Greenhouse API")
api = APIRouter(prefix="/api")


# ---------- Models ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SensorReadingIn(BaseModel):
    temperature: float  # Celsius
    humidity: float  # %
    soil_moisture: float  # %
    light: float  # lux (or %)
    co2: float  # ppm


class SensorReadingOut(SensorReadingIn):
    id: str
    timestamp: datetime


class AlertIn(BaseModel):
    disease: str
    confidence: float  # 0..1
    severity: str = "warning"  # 'info' | 'warning' | 'error'
    plant_zone: Optional[str] = None
    description: Optional[str] = None
    recommendations: Optional[List[str]] = None
    image_base64: Optional[str] = None  # base64 image data
    image_url: Optional[str] = None


class AlertOut(BaseModel):
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


# ---------- Auth helpers ----------
def hash_password(p: str) -> str:
    return pwd.hash(p)


def verify_password(p: str, h: str) -> bool:
    return pwd.verify(p, h)


def create_access_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET, algorithm=JWT_ALGO)


async def get_current_user(authorization: Optional[str] = Header(None)):
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
    user = await db.users.find_one({"_id": user_id}, {"password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


# ---------- Startup ----------
@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.alerts.create_index([("created_at", -1)])
    await db.sensor_readings.create_index([("timestamp", -1)])

    # Seed demo user
    demo_email = "demo@estufa.com"
    existing = await db.users.find_one({"email": demo_email})
    if not existing:
        await db.users.insert_one({
            "_id": uuid.uuid4().hex,
            "email": demo_email,
            "name": "Produtor Demo",
            "password_hash": hash_password("demo1234"),
            "created_at": datetime.now(timezone.utc),
        })
        logger.info("Seeded demo user: demo@estufa.com / demo1234")

    # Seed initial sensor reading if empty
    count = await db.sensor_readings.count_documents({})
    if count == 0:
        now = datetime.now(timezone.utc)
        for i in range(24):
            reading = {
                "_id": uuid.uuid4().hex,
                "temperature": round(22 + random.uniform(-2, 3), 1),
                "humidity": round(65 + random.uniform(-5, 10), 1),
                "soil_moisture": round(58 + random.uniform(-8, 8), 1),
                "light": round(720 + random.uniform(-100, 200), 0),
                "co2": round(420 + random.uniform(-20, 60), 0),
                "timestamp": now - timedelta(hours=23 - i),
            }
            await db.sensor_readings.insert_one(reading)
        logger.info("Seeded 24 sensor readings")

    # Seed a couple of demo alerts
    alerts_count = await db.alerts.count_documents({})
    if alerts_count == 0:
        demo_alerts = [
            {
                "_id": uuid.uuid4().hex,
                "disease": "Míldio (Downy Mildew)",
                "confidence": 0.92,
                "severity": "error",
                "plant_zone": "Bancada A - Fileira 3",
                "description": "Manchas amareladas na face superior das folhas com mofo cinza-esbranquiçado na face inferior. Detectado precocemente pela visão computacional.",
                "recommendations": [
                    "Reduzir a umidade relativa abaixo de 70%",
                    "Aumentar a ventilação da estufa",
                    "Aplicar fungicida à base de cobre nas plantas afetadas",
                    "Remover folhas gravemente infectadas",
                ],
                "image_url": "https://images.pexels.com/photos/3016319/pexels-photo-3016319.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
                "read": False,
                "resolved": False,
                "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
            },
            {
                "_id": uuid.uuid4().hex,
                "disease": "Septoriose",
                "confidence": 0.76,
                "severity": "warning",
                "plant_zone": "Bancada B - Fileira 1",
                "description": "Pequenas lesões circulares com centro cinza e bordas escuras nas folhas mais velhas.",
                "recommendations": [
                    "Isolar as plantas afetadas",
                    "Evitar irrigação por aspersão",
                    "Monitorar plantas vizinhas nas próximas 48h",
                ],
                "image_url": "https://images.pexels.com/photos/1400172/pexels-photo-1400172.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
                "read": False,
                "resolved": False,
                "created_at": datetime.now(timezone.utc) - timedelta(hours=8),
            },
            {
                "_id": uuid.uuid4().hex,
                "disease": "Podridão de Sclerotinia",
                "confidence": 0.68,
                "severity": "warning",
                "plant_zone": "Bancada C - Fileira 2",
                "description": "Sinais iniciais de podridão na base das plantas.",
                "recommendations": [
                    "Reduzir irrigação",
                    "Melhorar drenagem do substrato",
                ],
                "image_url": "https://images.pexels.com/photos/1656663/pexels-photo-1656663.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
                "read": True,
                "resolved": True,
                "created_at": datetime.now(timezone.utc) - timedelta(days=1, hours=3),
            },
        ]
        await db.alerts.insert_many(demo_alerts)
        logger.info("Seeded demo alerts")


@app.on_event("shutdown")
async def shutdown():
    client.close()


# ---------- Auth routes ----------
@api.post("/auth/register", response_model=TokenOut)
async def register(payload: RegisterIn):
    email = payload.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user_id = uuid.uuid4().hex
    await db.users.insert_one({
        "_id": user_id,
        "email": email,
        "name": payload.name,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc),
    })
    token = create_access_token(user_id)
    return TokenOut(
        access_token=token,
        user=UserOut(id=user_id, email=email, name=payload.name),
    )


@api.post("/auth/login", response_model=TokenOut)
async def login(payload: LoginIn):
    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token(user["_id"])
    return TokenOut(
        access_token=token,
        user=UserOut(id=user["_id"], email=user["email"], name=user.get("name")),
    )


@api.get("/auth/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut(id=user["_id"], email=user["email"], name=user.get("name"))


# ---------- Sensor routes ----------
@api.get("/sensors/latest", response_model=Optional[SensorReadingOut])
async def latest_sensor(user=Depends(get_current_user)):
    doc = await db.sensor_readings.find_one({}, sort=[("timestamp", -1)])
    if not doc:
        return None
    return SensorReadingOut(
        id=doc["_id"],
        temperature=doc["temperature"],
        humidity=doc["humidity"],
        soil_moisture=doc["soil_moisture"],
        light=doc["light"],
        co2=doc["co2"],
        timestamp=doc["timestamp"],
    )


@api.get("/sensors/history", response_model=List[SensorReadingOut])
async def sensor_history(limit: int = 24, user=Depends(get_current_user)):
    cursor = db.sensor_readings.find({}, sort=[("timestamp", -1)]).limit(limit)
    docs = await cursor.to_list(length=limit)
    docs.reverse()
    return [
        SensorReadingOut(
            id=d["_id"],
            temperature=d["temperature"],
            humidity=d["humidity"],
            soil_moisture=d["soil_moisture"],
            light=d["light"],
            co2=d["co2"],
            timestamp=d["timestamp"],
        )
        for d in docs
    ]


@api.post("/sensors/data", response_model=SensorReadingOut)
async def push_sensor_data(payload: SensorReadingIn):
    """Public endpoint for the physical greenhouse sensor / gateway to POST readings."""
    doc = {
        "_id": uuid.uuid4().hex,
        **payload.dict(),
        "timestamp": datetime.now(timezone.utc),
    }
    await db.sensor_readings.insert_one(doc)
    return SensorReadingOut(
        id=doc["_id"],
        temperature=doc["temperature"],
        humidity=doc["humidity"],
        soil_moisture=doc["soil_moisture"],
        light=doc["light"],
        co2=doc["co2"],
        timestamp=doc["timestamp"],
    )


# ---------- Alerts routes ----------
@api.get("/alerts", response_model=List[AlertOut])
async def list_alerts(unread_only: bool = False, user=Depends(get_current_user)):
    q = {"read": False} if unread_only else {}
    cursor = db.alerts.find(q, sort=[("created_at", -1)]).limit(100)
    docs = await cursor.to_list(length=100)
    return [_alert_out(d) for d in docs]


@api.get("/alerts/unread-count")
async def unread_count(user=Depends(get_current_user)):
    n = await db.alerts.count_documents({"read": False})
    return {"count": n}


@api.get("/alerts/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: str, user=Depends(get_current_user)):
    doc = await db.alerts.find_one({"_id": alert_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    # Mark as read when opened
    if not doc.get("read"):
        await db.alerts.update_one({"_id": alert_id}, {"$set": {"read": True}})
        doc["read"] = True
    return _alert_out(doc)


@api.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(alert_id: str, user=Depends(get_current_user)):
    res = await db.alerts.find_one_and_update(
        {"_id": alert_id},
        {"$set": {"resolved": True, "read": True}},
        return_document=True,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    doc = await db.alerts.find_one({"_id": alert_id})
    return _alert_out(doc)


@api.post("/alerts/webhook", response_model=AlertOut)
async def alert_webhook(payload: AlertIn):
    """Public webhook for the external computer-vision API to push disease detections."""
    doc = {
        "_id": uuid.uuid4().hex,
        "disease": payload.disease,
        "confidence": payload.confidence,
        "severity": payload.severity,
        "plant_zone": payload.plant_zone,
        "description": payload.description,
        "recommendations": payload.recommendations or [],
        "image_base64": payload.image_base64,
        "image_url": payload.image_url,
        "read": False,
        "resolved": False,
        "created_at": datetime.now(timezone.utc),
    }
    await db.alerts.insert_one(doc)
    return _alert_out(doc)


def _alert_out(d) -> AlertOut:
    return AlertOut(
        id=d["_id"],
        disease=d["disease"],
        confidence=d["confidence"],
        severity=d.get("severity", "warning"),
        plant_zone=d.get("plant_zone"),
        description=d.get("description"),
        recommendations=d.get("recommendations", []),
        image_base64=d.get("image_base64"),
        image_url=d.get("image_url"),
        read=d.get("read", False),
        resolved=d.get("resolved", False),
        created_at=d["created_at"],
    )


# ---------- Health ----------
@api.get("/")
async def root():
    return {"status": "ok", "service": "AlfaceAI Greenhouse API"}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

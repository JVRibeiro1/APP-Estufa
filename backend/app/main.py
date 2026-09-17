import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, sensors, vision

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="AlfaceAI Greenhouse API - SQL Server Version")
api = APIRouter(prefix="/api")


@api.get("/")
async def root():
    return {"status": "ok", "service": "AlfaceAI Greenhouse API - SQL Server"}


api.include_router(auth.router)
api.include_router(sensors.router)
api.include_router(vision.router)
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
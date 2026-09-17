from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, Numeric, String

from app.database import Base


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
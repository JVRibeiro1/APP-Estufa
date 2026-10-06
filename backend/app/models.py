from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, Numeric, String,ForeignKey
from app.database import Base


class UsuarioDB(Base):
    __tablename__ = "Usuarios"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Email = Column(String(255), unique=True, index=True, nullable=False)
    Nome = Column(String(255), nullable=True)
    SenhaHash = Column(String(255), nullable=False)
    Adm = Column(Boolean, nullable=False, default=False)
    DataCriacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    PushToken = Column(String(255), nullable=True)

class SensorReadingDB(Base):
    __tablename__ = "LeiturasSensores"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    IdEstufa = Column(Integer, ForeignKey("Estufas.Id"), nullable=False, default=1) 
    DeviceId = Column(String(50), nullable=False)
    Temperatura = Column(Numeric(5, 2), nullable=True)
    Umidade = Column(Numeric(5, 2), nullable=True)
    DataHoraEnvio = Column(DateTime, nullable=False, index=True)
    DataHoraGravacao = Column(DateTime, nullable=True)
    TempTeto = Column(Numeric(5, 2), nullable=True)
    UmidTeto = Column(Numeric(5, 2), nullable=True)


class DeteccaoInferenciaDB(Base):
    __tablename__ = "Deteccoes"  

    Id = Column(Integer, primary_key=True, autoincrement=True)
    EstufaId = Column(Integer, ForeignKey("Estufas.Id"), nullable=False)
    ImagemBlob = Column(String(500), nullable=True)
    Classe = Column(String(100), nullable=True)
    Confianca = Column(Numeric(5, 4), nullable=True)
    ProbBacteriano = Column(Numeric(5, 4), nullable=True)
    ProbFungico = Column(Numeric(5, 4), nullable=True)
    ProbSaudavel = Column(Numeric(5, 4), nullable=True)
    PatogenoDetectado = Column(Boolean, default=False)
    Alerta = Column(Boolean, default=False)
    ModeloVersao = Column(String(100), nullable=True)
    TempoInferenciaMs = Column(Numeric(10, 3), nullable=True)
    DataHoraDeteccao = Column(DateTime, nullable=False)
    DataHoraGravacao = Column(DateTime, nullable=True)
    BboxX = Column(Float, nullable=True)
    BboxY = Column(Float, nullable=True)
    BboxW = Column(Float, nullable=True)
    BboxH = Column(Float, nullable=True)
    HeatmapBlob = Column(String(500), nullable=True)
    Lido = Column(Boolean, nullable=True, default=False)
    Resolvido = Column(Boolean, nullable=True, default=None)

class EstufaDB(Base):
    __tablename__ = "Estufas"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    NomeEstufa = Column(String(255), nullable=False)
    DataCriacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UsuarioEstufaDB(Base):
    __tablename__ = "UsuarioEstufa"

    UsuarioId = Column(Integer, ForeignKey("Usuarios.Id"), primary_key=True)
    EstufaId = Column(Integer, ForeignKey("Estufas.Id"), primary_key=True)
    DataVinculo = Column(DateTime, default=lambda: datetime.now(timezone.utc))
import os
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Definições do banco de dados (Azure SQL Database)
SERVER = os.environ.get("DB_SERVER", "canada-tcc.database.windows.net")
DATABASE = os.environ.get("DB_NAME", "EstufaTCC")
DB_USER = os.environ.get("DB_USER", "cadanaTCC")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "unipG826HA2")
DRIVER = os.environ.get("DB_DRIVER", "ODBC Driver 18 for SQL Server")

# String de conexão ODBC com autenticação SQL e SSL ativo
odbc_str = (
    f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};"
    f"UID={DB_USER};PWD={DB_PASSWORD};"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"mssql+aioodbc:///?odbc_connect={urllib.parse.quote_plus(odbc_str)}",
)

JWT_SECRET = os.environ.get("JWT_SECRET", "alface-ai-dev-secret-change-me")
JWT_ALGO = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 24 * 7
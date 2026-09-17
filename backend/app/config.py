import os
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

SERVER = os.environ.get("DB_SERVER", "localhost\\SQLEXPRESS")
DATABASE = os.environ.get("DB_NAME", "app_homolog")
DRIVER = "ODBC Driver 18 for SQL Server"

odbc_str = (
    f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};"
    "Trusted_Connection=yes;TrustServerCertificate=yes;"
)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"mssql+aioodbc:///?odbc_connect={urllib.parse.quote_plus(odbc_str)}",
)

JWT_SECRET = os.environ.get("JWT_SECRET", "alface-ai-dev-secret-change-me")
JWT_ALGO = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 24 * 7
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # Consulta DNI (RENIEC) - fuente principal + contingencias
    reniec_api_url: str = os.getenv("RENIEC_API_URL", "https://api.decolecta.com/v1/reniec/dni")
    reniec_api_token: str = os.getenv("RENIEC_API_TOKEN", "")
    perudevs_dni_url: str = os.getenv("PERUDEVS_DNI_URL", "https://api.perudevs.com/api/v1/dni/simple")
    perudevs_dni_token: str = os.getenv("PERUDEVS_DNI_TOKEN", "")
    apiperu_dni_url: str = os.getenv("APIPERU_DNI_URL", "https://apiperu.dev/api/dni")
    apiperu_dni_token: str = os.getenv("APIPERU_DNI_TOKEN", "")
    
    # App settings
    app_name: str = "Generador de Preguntas DREHCO"
    debug: bool = False

    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "https://sieva.drehuanuco.gob.pe",
        "http://sieva.drehuanuco.gob.pe"
    ]

    # Base de datos
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/lectosistem_dre"
    )

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8  # 8 hours

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignorar variables de entorno no declaradas


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

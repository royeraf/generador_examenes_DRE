from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Google Gemini - clave principal + contingencias (misma cuota gratuita
    # se agota rápido en free tier; se rota a la siguiente clave en un 429)
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_api_key_2: str = os.getenv("GOOGLE_API_KEY_2", "")
    google_api_key_3: str = os.getenv("GOOGLE_API_KEY_3", "")

    # Modelos Gemini en orden de preferencia. Google retira modelos del free
    # tier (404 "no longer available to new users") y los nuevos suelen volver
    # 503 por alta demanda, así que se baja a la siguiente opción y finalmente
    # se reintenta un segundo pase. Se sobreescribe con GEMINI_MODELS=a,b,c
    gemini_models: str = os.getenv(
        "GEMINI_MODELS",
        "gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash,gemini-2.5-flash,"
        "gemini-3.5-flash-lite,gemini-flash-latest",
    )

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

    @property
    def google_api_keys(self) -> list[str]:
        """Claves de Gemini en orden de prioridad, sin las vacías."""
        return [k for k in (self.google_api_key, self.google_api_key_2, self.google_api_key_3) if k]

    @property
    def gemini_model_list(self) -> list[str]:
        """Modelos Gemini en orden de preferencia, sin las entradas vacías."""
        return [
            nombre.strip().removeprefix("models/")
            for nombre in self.gemini_models.split(",")
            if nombre.strip()
        ]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

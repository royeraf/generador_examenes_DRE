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
    
    # App settings
    app_name: str = "Generador de Preguntas DREHCO"
    debug: bool = True
    
    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:5174", 
        "http://127.0.0.1:5174",
        "http://localhost:5175", 
        "http://127.0.0.1:5175",
        "https://generador-examenes-dre.onrender.com"
    ]
    
    class Config:
        env_file = ".env"

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

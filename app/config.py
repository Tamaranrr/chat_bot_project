import os
from dotenv import load_dotenv
load_dotenv(override=True)

def _get(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip() or default

class Settings:
    APP_ENV = _get("APP_ENV", "development")                
    API_TITLE = _get("API_TITLE", "Chatbot IA – API")
    API_VERSION = _get("API_VERSION", "0.1.0")

    # Base de datos (SQLite por defecto)
    DATABASE_URL = _get("DATABASE_URL", "sqlite:///./app/chatbot.db")
    DB_SCHEMA = _get("DB_SCHEMA", "public")

    # Logging
    LOG_LEVEL = _get("LOG_LEVEL", "INFO")                  

    # Bot / NLP
    LOW_CONFIDENCE_THRESHOLD = float(_get("LOW_CONFIDENCE_THRESHOLD", "0.45"))
    MISUNDERSTAND_LIMIT = int(_get("MISUNDERSTAND_LIMIT", "2"))

settings = Settings()

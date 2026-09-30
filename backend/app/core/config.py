import logging
import os
import secrets
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("enotecamolise")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "EnotecaMolise API"
    API_V1_STR: str = "/api/v1"

    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "enoteca_molise"

    # Nessun valore predefinito: se manca nel .env viene generata una chiave casuale
    # (i token scadono a ogni riavvio) e viene mostrato un avviso.
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 4320

    UPLOAD_DIR: str = os.path.join(BACKEND_DIR, "uploads")

    # Origini autorizzate per CORS (separate da virgola nel .env)
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Credenziali per creare l'admin iniziale (solo se non esiste ancora)
    ADMIN_EMAIL: str = "admin@enotecamolise.it"
    ADMIN_PASSWORD: Optional[str] = None

    # Popola il DB con dati di esempio quando e' vuoto (solo sviluppo)
    SEED_SAMPLE_DATA: bool = False

    # Le nuove cantine registrate restano in attesa di approvazione dell'admin
    AUTO_APPROVE_PRODUCERS: bool = False

    # Estrazione IA delle schede vino da PDF.
    # AI_PROVIDER: "auto" (usa la prima chiave disponibile), "gemini" oppure "anthropic"
    AI_PROVIDER: str = "auto"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    # Modelli usati in automatico se il principale e' sovraccarico o ha finito la quota gratuita
    GEMINI_FALLBACK_MODELS: str = "gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-5-5"
    AI_TIMEOUT_SECONDS: int = 180

    # Limiti anti-abuso
    LOGIN_MAX_ATTEMPTS: int = 10
    LOGIN_WINDOW_SECONDS: int = 900
    INQUIRY_MAX_PER_WINDOW: int = 5
    INQUIRY_WINDOW_SECONDS: int = 600

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @field_validator("UPLOAD_DIR", mode="after")
    @classmethod
    def absolute_upload_dir(cls, v):
        return v if os.path.isabs(v) else os.path.join(BACKEND_DIR, v)


settings = Settings()

if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
    logger.warning(
        "SECRET_KEY assente o troppo corta nel .env: uso una chiave casuale temporanea. "
        "Tutte le sessioni scadranno al riavvio. Genera una chiave con: "
        "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )
    settings.SECRET_KEY = secrets.token_urlsafe(64)

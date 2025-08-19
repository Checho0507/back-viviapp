from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de datos
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://admin:1234*@localhost/mibasedatos")

    # CORS
    cors_origins: List[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]

    # Zona horaria de la app
    app_tz: str = os.getenv("APP_TZ", "America/Bogota")

    # Proveedor de WhatsApp ("twilio" | "meta")
    whatsapp_provider: str = os.getenv("WHATSAPP_PROVIDER", "twilio").lower()

    # Twilio
    twilio_account_sid: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token: str | None = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_whatsapp_from: str | None = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    whatsapp_to: str | None = os.getenv("WHATSAPP_TO")  # e.g., whatsapp:+57...

    # Meta WhatsApp Cloud
    whatsapp_meta_token: str | None = os.getenv("WHATSAPP_META_TOKEN")
    whatsapp_meta_phone_id: str | None = os.getenv("WHATSAPP_META_PHONE_ID")
    whatsapp_to_plain: str | None = os.getenv("WHATSAPP_TO_PLAIN")  # e.g., +57...

settings = Settings()
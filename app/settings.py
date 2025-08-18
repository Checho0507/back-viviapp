from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de datos
    database_url: str

    # CORS
    cors_origins: List[str] = ["http://localhost:5173"]

    # Zona horaria de la app
    app_tz: str = "America/Bogota"

    # Proveedor de WhatsApp ("twilio" | "meta")
    whatsapp_provider: str = "twilio"

    # Twilio
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str | None = "whatsapp:+14155238886"
    whatsapp_to: str | None = None  # e.g., whatsapp:+57...

    # Meta WhatsApp Cloud
    whatsapp_meta_token: str | None = None
    whatsapp_meta_phone_id: str | None = None
    whatsapp_to_plain: str | None = None  # e.g., +57...


settings = Settings()

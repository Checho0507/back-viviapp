from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, SecretStr
from typing import List
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de datos
    database_url: str = "postgresql+psycopg2://checho:o5936ATJxThofG2jwElI5wzZfuhpslot@dpg-d2hq9pm3jp1c738lktsg-a/pedidos_00mw?sslmode=require"

    # CORS
    cors_origins: List[str] = ["https://back-viviapp.onrender.com"]

    # Zona horaria de la app
    app_tz: str = "America/Bogota"

    # Proveedor de WhatsApp
    whatsapp_provider: str = "twilio"

    # Twilio
    twilio_account_sid: str | None = None
    twilio_auth_token: SecretStr | None = None
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    whatsapp_to: str | None = None  # e.g., whatsapp:+57...

    # Meta WhatsApp Cloud
    whatsapp_meta_token: SecretStr | None = None
    whatsapp_meta_phone_id: str | None = None
    whatsapp_to_plain: str | None = None  # e.g., +57...

    @field_validator("cors_origins", mode="before")
    def split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    @field_validator("whatsapp_provider")
    def normalize_provider(cls, v):
        return v.lower()

settings = Settings()

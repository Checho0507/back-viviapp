from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .settings import settings

# Intentar usar la zona horaria configurada, con fallback a UTC
try:
    TZ = ZoneInfo(settings.app_tz)
except ZoneInfoNotFoundError:
    TZ = ZoneInfo("UTC")

def formatear_fecha_col(fecha: date | datetime, formato: str = "%d/%m/%Y") -> str:
    """
    Devuelve la fecha (o datetime) formateada según la zona horaria de la app.
    Si es datetime, la convierte a TZ antes de formatear.
    """
    if isinstance(fecha, datetime):
        fecha = fecha.astimezone(TZ)
    return fecha.strftime(formato)

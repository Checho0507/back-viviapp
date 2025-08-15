from datetime import date
import zoneinfo
from .settings import settings

TZ = zoneinfo.ZoneInfo(settings.app_tz)

def formatear_fecha_col(fecha: date) -> str:
    return fecha.strftime("%d/%m/%Y")
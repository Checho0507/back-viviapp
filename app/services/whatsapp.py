from dataclasses import dataclass
from decimal import Decimal
import httpx

from ..schemas import ResumenDia
from ..utils import formatear_fecha_col
from ..settings import settings

@dataclass
class WhatsAppResult:
    ok: bool
    provider: str
    detail: dict | None = None
    error: str | None = None


def _armar_mensaje(resumen: ResumenDia) -> str:
    lineas = [
        f"✅ Resumen pedidos del {formatear_fecha_col(resumen.fecha)}",
        f"Total: ${resumen.total:,.2f}",
        f"Cantidad: {resumen.cantidad}",
        "",
        "Detalle por distribuidor:",
    ]
    if not resumen.por_distribuidor:
        lineas.append("(Sin pedidos registrados)")
    else:
        for item in resumen.por_distribuidor:
            lineas.append(f"- {item.distribuidor}: ${item.total:,.2f} ({item.cantidad})")
    return "\n".join(lineas)


async def send_whatsapp(resumen: ResumenDia) -> WhatsAppResult:
    provider = settings.whatsapp_provider
    message = _armar_mensaje(resumen)

    if provider == "twilio":
        return await _send_twilio(message)
    elif provider == "meta":
        return await _send_meta(message)
    else:
        return WhatsAppResult(ok=False, provider=provider, error="Proveedor WhatsApp no soportado")


async def _send_twilio(message: str) -> WhatsAppResult:
    if not (
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_whatsapp_from
        and settings.whatsapp_to
    ):
        return WhatsAppResult(ok=False, provider="twilio", error="Faltan credenciales Twilio en .env")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)

    data = {
        "From": settings.twilio_whatsapp_from,
        "To": settings.whatsapp_to,
        "Body": message,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, data=data, auth=auth)
        if resp.status_code in (200, 201):
            return WhatsAppResult(ok=True, provider="twilio", detail=resp.json())
        return WhatsAppResult(ok=False, provider="twilio", error=f"{resp.status_code} {resp.text}")


async def _send_meta(message: str) -> WhatsAppResult:
    if not (
        settings.whatsapp_meta_token
        and settings.whatsapp_meta_phone_id
        and settings.whatsapp_to_plain
    ):
        return WhatsAppResult(ok=False, provider="meta", error="Faltan credenciales Meta WhatsApp Cloud en .env")

    url = f"https://graph.facebook.com/v21.0/{settings.whatsapp_meta_phone_id}/messages"
    headers = {"Authorization": f"Bearer {settings.whatsapp_meta_token}"}
    json_payload = {
        "messaging_product": "whatsapp",
        "to": settings.whatsapp_to_plain,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=json_payload)
        if resp.status_code in (200, 201):
            return WhatsAppResult(ok=True, provider="meta", detail=resp.json())
        return WhatsAppResult(ok=False, provider="meta", error=f"{resp.status_code} {resp.text}")
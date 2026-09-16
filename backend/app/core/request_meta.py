"""Utilidades para extraer metadata de la petición (IP, dispositivo, SO, navegador)."""
from typing import Optional

from fastapi import Request


def get_client_ip(request: Request) -> Optional[str]:
    """Obtiene la IP real del cliente considerando proxies (nginx)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # El primer valor es la IP original del cliente
        ip = forwarded.split(",")[0].strip()
        if ip:
            return ip

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host
    return None


def parse_user_agent(user_agent: Optional[str]) -> dict:
    """Parser ligero de User-Agent (sin dependencias externas)."""
    ua = user_agent or ""
    ua_lower = ua.lower()

    # ── Dispositivo ──────────────────────────────────────────────────────────
    if any(k in ua_lower for k in ("ipad", "tablet", "kindle", "silk", "playbook")):
        dispositivo = "tablet"
    elif any(k in ua_lower for k in ("mobi", "android", "iphone", "ipod", "windows phone")):
        dispositivo = "mobile"
    else:
        dispositivo = "desktop"

    # ── Sistema operativo ────────────────────────────────────────────────────
    if "windows" in ua_lower:
        so = "Windows"
    elif "android" in ua_lower:
        so = "Android"
    elif any(k in ua_lower for k in ("iphone", "ipad", "ipod", "ios")):
        so = "iOS"
    elif "mac os x" in ua_lower or "macintosh" in ua_lower:
        so = "macOS"
    elif "cros" in ua_lower:
        so = "ChromeOS"
    elif "linux" in ua_lower:
        so = "Linux"
    else:
        so = "Desconocido"

    # ── Navegador (orden importa) ────────────────────────────────────────────
    if "edg" in ua_lower or "edgios" in ua_lower or "edga" in ua_lower:
        navegador = "Edge"
    elif "opr" in ua_lower or "opera" in ua_lower:
        navegador = "Opera"
    elif "chrome" in ua_lower and "chromium" not in ua_lower:
        navegador = "Chrome"
    elif "chromium" in ua_lower:
        navegador = "Chromium"
    elif "firefox" in ua_lower or "fxios" in ua_lower:
        navegador = "Firefox"
    elif "safari" in ua_lower:
        navegador = "Safari"
    elif "msie" in ua_lower or "trident" in ua_lower:
        navegador = "Internet Explorer"
    else:
        navegador = "Desconocido"

    return {
        "dispositivo": dispositivo,
        "sistema_operativo": so,
        "navegador": navegador,
        "es_movil": dispositivo == "mobile",
    }

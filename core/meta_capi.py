"""Meta Conversions API — wysyłka zdarzenia "Lead" z formularza kontaktowego
bezpośrednio z serwera do Meta, jako uzupełnienie zwykłego Pixela z
przeglądarki (patrz core/static/core/js/cookie-consent.js). Serwer widzi
zapytanie niezależnie od tego, czy przeglądarka użytkownika zablokowała
Pixel (AdBlock, ITP na Safari/iOS) — dzięki temu Meta ma pełniejsze dane do
optymalizacji kampanii.

Aktywne tylko gdy META_PIXEL_ID i META_CAPI_ACCESS_TOKEN są ustawione (patrz
settings.py) — bez nich funkcja nic nie robi, więc lokalnie/bez konfiguracji
nic się nie psuje.
"""

import hashlib
import json
import logging
import time
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v21.0"


def _hash(value):
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def send_lead_event(contact_message, request, event_id):
    """Wysyła zdarzenie Lead. event_id musi być TAKI SAM jak w odpowiadającym
    mu zdarzeniu Pixel z przeglądarki (patrz core/views.py, home.html) —
    dzięki temu Meta zdeduplikuje je jako jedno zdarzenie, nie dwa."""
    if not (settings.META_PIXEL_ID and settings.META_CAPI_ACCESS_TOKEN):
        return

    user_data = {"em": [_hash(contact_message.email)]}
    if contact_message.phone:
        digits = "".join(ch for ch in contact_message.phone if ch.isdigit())
        if digits:
            user_data["ph"] = [_hash(digits)]

    client_ip = request.META.get("REMOTE_ADDR", "")
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    if client_ip:
        user_data["client_ip_address"] = client_ip

    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if user_agent:
        user_data["client_user_agent"] = user_agent

    fbc = request.COOKIES.get("_fbc")
    fbp = request.COOKIES.get("_fbp")
    if fbc:
        user_data["fbc"] = fbc
    if fbp:
        user_data["fbp"] = fbp

    payload = {
        "data": [
            {
                "event_name": "Lead",
                "event_time": int(time.time()),
                "event_id": event_id,
                "action_source": "website",
                "event_source_url": request.build_absolute_uri(),
                "user_data": user_data,
            }
        ],
        "access_token": settings.META_CAPI_ACCESS_TOKEN,
    }

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{settings.META_PIXEL_ID}/events"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        logger.error("Meta CAPI: błąd wysyłki zdarzenia Lead (%s): %s", exc.code, exc.read())
    except urllib.error.URLError:
        logger.exception("Meta CAPI: nie udało się wysłać zdarzenia Lead.")

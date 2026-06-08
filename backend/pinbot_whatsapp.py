"""
PinBot WhatsApp Business API v3 client.
Spec: WhatsApp_API_Pinned_Documentation.pdf (SpringEdge, Dec 2024 v3.0)

Endpoints used:
  POST {base}/{phone_number_id}/messages  — text (§1), location (§2), template (§8)
  GET  {base}/getuserdetails              — account verification (§26)
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import requests

logger = logging.getLogger("pinbot_whatsapp")


def recipient_digits(phone: str) -> str:
    """Doc samples use 91XXXXXXXXXX (country code + number, no +)."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        return f"91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return digits
    if len(digits) == 11 and digits.startswith("0"):
        return f"91{digits[1:]}"
    return digits


def messages_url(api_base: str, phone_number_id: str) -> str:
    return f"{api_base.rstrip('/')}/{phone_number_id}/messages"


def _headers(api_key: str) -> dict[str, str]:
    return {"Content-Type": "application/json", "apikey": api_key}


def _callback_data(event_type: str | None, extra: dict | None = None) -> str | None:
    if not event_type:
        return None
    payload = {"source": "franklin_crm", "event": event_type, **(extra or {})}
    return json.dumps(payload, separators=(",", ":"))[:512]


def build_text_payload(
    to: str,
    body: str,
    *,
    event_type: str | None = None,
) -> dict[str, Any]:
    """§1 Send Text Message."""
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "preview_url": False,
        "recipient_type": "individual",
        "to": recipient_digits(to),
        "type": "text",
        "text": {"body": body},
    }
    cb = _callback_data(event_type)
    if cb:
        payload["biz_opaque_callback_data"] = cb
    return payload


def build_location_payload(
    to: str,
    lat: float,
    lng: float,
    *,
    name: str = "",
    address: str = "",
    event_type: str | None = None,
) -> dict[str, Any]:
    """§2 Send Location Message."""
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_digits(to),
        "type": "location",
        "location": {
            "latitude": lat,
            "longitude": lng,
            "name": (name or "Field location")[:200],
            "address": (address or "")[:300],
        },
    }
    cb = _callback_data(event_type, {"lat": lat, "lng": lng})
    if cb:
        payload["biz_opaque_callback_data"] = cb
    return payload


def build_template_payload(
    to: str,
    template_name: str,
    params: list[str],
    *,
    language: str = "en",
    event_type: str | None = None,
) -> dict[str, Any]:
    """§8 Send Text Template Message (body parameters only)."""
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_digits(to),
        "type": "template",
        "template": {
            "language": {"code": language},
            "name": template_name,
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in params],
                }
            ],
        },
    }
    cb = _callback_data(event_type, {"template": template_name})
    if cb:
        payload["biz_opaque_callback_data"] = cb
    return payload


def _post_sync(url: str, payload: dict, api_key: str) -> dict[str, Any]:
    resp = requests.post(url, json=payload, headers=_headers(api_key), timeout=30)
    try:
        body = resp.json()
    except Exception:
        body = {"raw": (resp.text or "")[:500]}
    if resp.status_code >= 400:
        detail = body
        if isinstance(body, dict):
            detail = body.get("error") or body.get("message") or body
        raise RuntimeError(f"WhatsApp API HTTP {resp.status_code}: {detail}")
    return body if isinstance(body, dict) else {"response": body}


def _extract_message_id(data: dict) -> str | None:
    messages = data.get("messages") or []
    if messages and isinstance(messages[0], dict):
        return messages[0].get("id")
    return None


async def post_message(
    api_base: str,
    phone_number_id: str,
    api_key: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    url = messages_url(api_base, phone_number_id)
    return await asyncio.to_thread(_post_sync, url, payload, api_key)


async def send_text(
    to: str,
    body: str,
    *,
    api_base: str,
    phone_number_id: str,
    api_key: str,
    event_type: str | None = None,
) -> dict[str, Any]:
    payload = build_text_payload(to, body, event_type=event_type)
    data = await post_message(api_base, phone_number_id, api_key, payload)
    return {
        "status": "sent",
        "channel": "whatsapp",
        "to": to,
        "message_id": _extract_message_id(data),
        "provider_response": data,
        "api": "pinbot_v3_text",
    }


async def send_location(
    to: str,
    lat: float,
    lng: float,
    *,
    api_base: str,
    phone_number_id: str,
    api_key: str,
    name: str = "",
    address: str = "",
    event_type: str | None = None,
) -> dict[str, Any]:
    payload = build_location_payload(
        to, lat, lng, name=name, address=address, event_type=event_type
    )
    data = await post_message(api_base, phone_number_id, api_key, payload)
    return {
        "status": "sent",
        "channel": "whatsapp",
        "to": to,
        "message_id": _extract_message_id(data),
        "provider_response": data,
        "api": "pinbot_v3_location",
        "location": {"lat": lat, "lng": lng},
    }


async def send_template(
    to: str,
    template_name: str,
    params: list[str],
    *,
    api_base: str,
    phone_number_id: str,
    api_key: str,
    language: str = "en",
    event_type: str | None = None,
) -> dict[str, Any]:
    payload = build_template_payload(
        to, template_name, params, language=language, event_type=event_type
    )
    data = await post_message(api_base, phone_number_id, api_key, payload)
    return {
        "status": "sent",
        "channel": "whatsapp",
        "to": to,
        "message_id": _extract_message_id(data),
        "template": template_name,
        "provider_response": data,
        "api": "pinbot_v3_template",
    }


async def fetch_user_details(api_base: str, api_key: str) -> dict[str, Any]:
    """§26 Get user details — verify phone_number_id and WABA linkage."""
    url = f"{api_base.rstrip('/')}/getuserdetails"

    def _get() -> dict:
        resp = requests.get(url, headers=_headers(api_key), timeout=30)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": (resp.text or "")[:500]}
        if resp.status_code >= 400:
            raise RuntimeError(f"getuserdetails HTTP {resp.status_code}: {body}")
        return body if isinstance(body, dict) else {"response": body}

    return await asyncio.to_thread(_get)

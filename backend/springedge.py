"""SpringEdge SMS & WhatsApp integration (legacy web API + optional REST)."""
from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger("springedge")

API_KEY = os.environ.get("SPRINGEDGE_API_KEY", "").strip()
SENDER_ID = os.environ.get("SPRINGEDGE_SENDER_ID", "SPREDG").strip()
# Legacy API (resolves via web.springedge.com) — use this by default
LEGACY_SMS_URL = os.environ.get(
    "SPRINGEDGE_LEGACY_SMS_URL", "https://web.springedge.com/api/web/send"
).strip()
# REST API host api.springedge.com often does not resolve; only used if explicitly set
SMS_URL = os.environ.get("SPRINGEDGE_SMS_URL", "").strip()
WHATSAPP_URL = os.environ.get("SPRINGEDGE_WHATSAPP_URL", "").strip()
WHATSAPP_TEMPLATE = os.environ.get("SPRINGEDGE_WHATSAPP_TEMPLATE", "").strip()
WHATSAPP_PARAM_KEY = os.environ.get("SPRINGEDGE_WHATSAPP_PARAM_KEY", "message").strip()
API_STYLE = os.environ.get("SPRINGEDGE_API_STYLE", "legacy").strip().lower()
FORCE_MOCK = os.environ.get("SPRINGEDGE_MOCK", "false").lower() in ("1", "true", "yes")


def is_configured() -> bool:
    return bool(API_KEY) and not FORCE_MOCK


def normalize_phone(phone: str) -> str:
    """E.164 (+91...) for display/logging."""
    raw = (phone or "").strip()
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    if raw.startswith("+") and digits:
        return f"+{digits}"
    return f"+{digits}" if digits else ""


def phone_for_legacy(phone: str) -> str:
    """SpringEdge legacy API expects 91XXXXXXXXXX (no +)."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        return f"91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return digits
    if len(digits) == 11 and digits.startswith("0"):
        return f"91{digits[1:]}"
    return digits


def _friendly_error(exc: Exception) -> str:
    msg = str(exc)
    if "getaddrinfo failed" in msg or "Failed to resolve" in msg:
        return (
            "Cannot reach SpringEdge (api.springedge.com DNS failed). "
            "Set SPRINGEDGE_API_STYLE=legacy and restart the backend."
        )
    if "11001" in msg:
        return "SpringEdge host unreachable. Check internet/DNS."
    if "403" in msg or "Invalid API Key" in msg or "INVALID_API_KEY" in msg:
        return "SpringEdge rejected the API key. Copy it from dashboard Settings > API."
    if "422" in msg or "sender" in msg.lower() or "template" in msg.lower():
        return f"SpringEdge rejected the request: {msg[:200]}"
    return msg[:300]


def _parse_legacy_response(resp: requests.Response) -> dict:
    try:
        body = resp.json()
    except Exception:
        body = {"raw": (resp.text or "")[:500]}
    if resp.status_code >= 400:
        detail = body
        if isinstance(body, dict):
            detail = body.get("message") or body.get("error") or body.get("status") or body
        raise RuntimeError(f"SpringEdge HTTP {resp.status_code}: {detail}")
    return body if isinstance(body, dict) else {"response": body}


def _send_legacy_sms_sync(to: str, message: str) -> dict:
    to_digits = phone_for_legacy(to)
    if not to_digits or len(to_digits) < 12:
        raise ValueError(f"Invalid phone for SpringEdge: {to}")

    payload = {
        "apikey": API_KEY,
        "sender": SENDER_ID,
        "to": to_digits,
        "message": message,
        "format": "json",
    }
    # GET and POST both supported; POST avoids URL length limits
    resp = requests.post(LEGACY_SMS_URL, data=payload, timeout=30)
    return _parse_legacy_response(resp)


def _post_json_sync(url: str, payload: dict) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text[:500]}
    if resp.status_code >= 400:
        err = body.get("error") if isinstance(body, dict) else body
        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        raise RuntimeError(f"SpringEdge HTTP {resp.status_code}: {msg}")
    return body if isinstance(body, dict) else {"response": body}


async def _send_legacy_sms(to: str, message: str) -> dict:
    return await asyncio.to_thread(_send_legacy_sms_sync, to, message)


async def _send_rest_sms(to: str, message: str, msg_type: str = "transactional") -> dict:
    url = SMS_URL or "https://api.springedge.com/v1/sms/send"
    phone = normalize_phone(to)
    data = await asyncio.to_thread(
        _post_json_sync,
        url,
        {
            "to": phone,
            "sender_id": SENDER_ID,
            "message": message,
            "type": msg_type,
        },
    )
    return {
        "status": data.get("status", "sent"),
        "channel": "sms",
        "to": phone,
        "message_id": data.get("message_id"),
        "provider_response": data,
        "api": "rest",
    }


async def send_sms(to: str, message: str, msg_type: str = "transactional") -> dict[str, Any]:
    phone = normalize_phone(to)
    if not phone:
        return {"status": "skipped", "reason": "invalid_phone", "to": to}

    if not is_configured():
        logger.info("[SpringEdge mock SMS] %s: %s", phone, message[:120])
        return {"status": "mocked", "channel": "sms", "to": phone, "message": message}

    use_legacy = API_STYLE == "legacy" or not SMS_URL or "api.springedge.com" in (SMS_URL or "")

    if use_legacy:
        try:
            data = await _send_legacy_sms(phone, message)
            return {
                "status": data.get("status", data.get("Status", "sent")),
                "channel": "sms",
                "to": phone,
                "message_id": data.get("message_id") or data.get("MessageId"),
                "provider_response": data,
                "api": "legacy",
            }
        except Exception as e:
            logger.exception("SpringEdge legacy SMS failed")
            raise RuntimeError(_friendly_error(e)) from e

    try:
        return await _send_rest_sms(phone, message, msg_type)
    except Exception as e:
        if "resolve" in str(e).lower() or "getaddrinfo" in str(e).lower():
            logger.warning("REST SMS failed (DNS), retrying legacy API")
            data = await _send_legacy_sms(phone, message)
            return {
                "status": data.get("status", "sent"),
                "channel": "sms",
                "to": phone,
                "message_id": data.get("message_id"),
                "provider_response": data,
                "api": "legacy_fallback",
            }
        raise RuntimeError(_friendly_error(e)) from e


async def send_whatsapp(to: str, message: str) -> dict[str, Any]:
    phone = normalize_phone(to)
    if not phone:
        return {"status": "skipped", "reason": "invalid_phone", "to": to}

    if not is_configured():
        logger.info("[SpringEdge mock WhatsApp] %s: %s", phone, message[:120])
        return {"status": "mocked", "channel": "whatsapp", "to": phone, "message": message}

    # Native WhatsApp REST (api.springedge.com) is often unreachable — deliver via SMS
    prefix = f"[WhatsApp · {WHATSAPP_TEMPLATE}] " if WHATSAPP_TEMPLATE else "[WhatsApp follow-up] "
    body = f"{prefix}{message}"

    try:
        result = await send_sms(phone, body, msg_type="transactional")
        result["channel"] = "whatsapp_via_sms"
        if WHATSAPP_TEMPLATE:
            result["template"] = WHATSAPP_TEMPLATE
            result["note"] = (
                "Delivered as SMS (web.springedge.com). "
                "Native WhatsApp template API requires api.springedge.com DNS."
            )
        return result
    except Exception as e:
        raise RuntimeError(_friendly_error(e)) from e


async def send_message(to: str, message: str, channel: str = "sms") -> dict[str, Any]:
    ch = (channel or "sms").lower()
    if ch == "whatsapp":
        return await send_whatsapp(to, message)
    return await send_sms(to, message)

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
WABA_API_KEY = (os.environ.get("SPRINGEDGE_WABA_API_KEY") or API_KEY).strip()
PHONE_NUMBER_ID = os.environ.get("SPRINGEDGE_PHONE_NUMBER_ID", "").strip()
WHATSAPP_API_BASE = os.environ.get(
    "SPRINGEDGE_WHATSAPP_API_URL", "https://partnersv1.pinbot.ai/v3"
).strip()
SENDER_ID = os.environ.get("SPRINGEDGE_SENDER_ID", "SPREDG").strip()
# Legacy API (resolves via web.springedge.com) — use this by default
LEGACY_SMS_URL = os.environ.get(
    "SPRINGEDGE_LEGACY_SMS_URL", "https://web.springedge.com/api/web/send"
).strip()
# REST API host api.springedge.com often does not resolve; only used if explicitly set
SMS_URL = os.environ.get("SPRINGEDGE_SMS_URL", "").strip()
WHATSAPP_URL = os.environ.get("SPRINGEDGE_WHATSAPP_URL", "").strip()
WHATSAPP_TEMPLATE = os.environ.get("SPRINGEDGE_WHATSAPP_TEMPLATE", "").strip()
WHATSAPP_TEMPLATE_LANG = os.environ.get("SPRINGEDGE_WHATSAPP_TEMPLATE_LANG", "en").strip()
WHATSAPP_PARAM_KEY = os.environ.get("SPRINGEDGE_WHATSAPP_PARAM_KEY", "message").strip()
WHATSAPP_TEXT_FALLBACK = os.environ.get("SPRINGEDGE_WHATSAPP_TEXT_FALLBACK", "true").lower() in (
    "1", "true", "yes",
)
WHATSAPP_TEXT_ONLY = os.environ.get("SPRINGEDGE_WHATSAPP_TEXT_ONLY", "false").lower() in (
    "1", "true", "yes",
)
API_STYLE = os.environ.get("SPRINGEDGE_API_STYLE", "legacy").strip().lower()
FORCE_MOCK = os.environ.get("SPRINGEDGE_MOCK", "false").lower() in ("1", "true", "yes")
DEMO_SMS_MODE = os.environ.get("SPRINGEDGE_DEMO_SMS", "").lower() in ("1", "true", "yes") or SENDER_ID == "SEDEMO"
DEMO_SMS_TEMPLATE = os.environ.get(
    "SPRINGEDGE_DEMO_SMS_TEMPLATE",
    "Hello {name}, This is a test message from spring edge",
).strip()


def is_configured() -> bool:
    return bool(API_KEY) and not FORCE_MOCK


def whatsapp_configured() -> bool:
    """PinBot / SpringEdge WhatsApp Business API (see WhatsApp_API_Pinned_Documentation.pdf)."""
    return bool(WABA_API_KEY and PHONE_NUMBER_ID) and not FORCE_MOCK


def format_demo_sms(recipient_name: str = "Customer") -> str:
    """Trial transactional account only allows this fixed body pattern."""
    name = sanitize_template_text(recipient_name or "Customer", max_len=40) or "Customer"
    return DEMO_SMS_TEMPLATE.replace("$var", name).replace("{name}", name)


def _recipient_name_for_demo(
    message: str,
    template_params: list[str] | None = None,
) -> str:
    if template_params and template_params[0]:
        return template_params[0]
    words = (message or "").strip().split()
    return words[0][:40] if words else "Customer"


def status_detail() -> dict[str, Any]:
    return {
        "sms_configured": is_configured(),
        "whatsapp_configured": whatsapp_configured(),
        "mock_mode": FORCE_MOCK or not API_KEY,
        "demo_sms_mode": DEMO_SMS_MODE,
        "whatsapp_sms_fallback": True,
        "demo_sms_template": DEMO_SMS_TEMPLATE if DEMO_SMS_MODE else None,
        "sender_id": SENDER_ID or None,
        "phone_number_id": PHONE_NUMBER_ID or None,
        "whatsapp_api": WHATSAPP_API_BASE if whatsapp_configured() else None,
        "whatsapp_template": WHATSAPP_TEMPLATE or None,
        "whatsapp_template_lang": WHATSAPP_TEMPLATE_LANG or None,
        "whatsapp_text_fallback": WHATSAPP_TEXT_FALLBACK,
        "whatsapp_text_only": WHATSAPP_TEXT_ONLY,
        "whatsapp_template_params": ["notification_alert", "msg_body"],
        "whatsapp_doc": "WhatsApp_API_Pinned_Documentation.pdf",
        "pinbot_endpoints": {
            "messages": f"{WHATSAPP_API_BASE.rstrip('/')}/{PHONE_NUMBER_ID}/messages" if whatsapp_configured() else None,
            "getuserdetails": f"{WHATSAPP_API_BASE.rstrip('/')}/getuserdetails" if whatsapp_configured() else None,
        },
    }


def sanitize_template_text(text: str, *, max_len: int = 450) -> str:
    """Strip chars that trigger Meta template error 135000; keep message readable."""
    s = (text or "").strip()
    replacements = {
        "₹": "Rs.",
        "—": "-",
        "→": "->",
        "•": "-",
        "\n": " ",
        "\r": " ",
        "\t": " ",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    s = re.sub(r"[^\x20-\x7E]", "", s)
    s = re.sub(r" {2,}", " ", s).strip()
    return s[:max_len]


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
    if "135000" in msg:
        return (
            "WhatsApp template blocked by Meta (error 135000). "
            "Recreate lms_notification in PinBot/Meta, or use text fallback."
        )
    if "422" in msg or "sender" in msg.lower() or "template" in msg.lower():
        return f"SpringEdge rejected the request: {msg[:200]}"
    return msg[:300]


def format_lms_notification_body(alert: str, msg: str) -> str:
    """
    lms_notification (English, Utility):
      Header (fixed): lms notification
      Body: Notification Alert: {{1}} / Msg: {{2}} / Thanks, LMS Tech Team
    Used for WhatsApp text fallback when Meta returns template error 135000.
    """
    a = sanitize_template_text(alert or "Franklin Wardcorpp Alert", max_len=200)
    m = sanitize_template_text(msg or "", max_len=450)
    return (
        "*lms notification*\n\n"
        f"Notification Alert: {a}\n"
        f"Msg: {m}\n"
        "Thanks, LMS Tech Team"
    )


def _whatsapp_text_from_template_params(params: list[str] | None, message: str) -> str:
    alert = (params[0] if params else "") or "Franklin Wardcorpp Alert"
    body = (params[1] if params and len(params) > 1 else message) or message
    return format_lms_notification_body(alert, body)


def _is_template_send_error(exc: Exception) -> bool:
    msg = str(exc)
    return any(code in msg for code in ("135000", "132000", "132001", "131058"))


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
    }
    # instantalerts.co trial API uses GET; web.springedge.com accepts POST
    if "instantalerts.co" in LEGACY_SMS_URL:
        resp = requests.get(LEGACY_SMS_URL, params=payload, timeout=30)
    else:
        payload["format"] = "json"
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


async def send_sms(
    to: str,
    message: str,
    msg_type: str = "transactional",
    *,
    recipient_name: str | None = None,
) -> dict[str, Any]:
    phone = normalize_phone(to)
    if not phone:
        return {"status": "skipped", "reason": "invalid_phone", "to": to}

    if DEMO_SMS_MODE:
        message = format_demo_sms(recipient_name or "Customer")

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


def _pinbot_cfg() -> dict[str, str]:
    return {
        "api_base": WHATSAPP_API_BASE,
        "phone_number_id": PHONE_NUMBER_ID,
        "api_key": WABA_API_KEY,
    }


def _whatsapp_delivery_failed(result: dict[str, Any] | None) -> bool:
    if not result:
        return True
    if result.get("delivery_mode") == "whatsapp_sms_fallback":
        return False
    status = (result.get("status") or "").lower()
    if status in ("sent", "queued", "awaited-dlr"):
        return False
    return status in ("failed", "skipped", "mocked", "unknown", "")


async def mandatory_sms_fallback(
    phone: str,
    message: str,
    *,
    template_params: list[str] | None = None,
    reason: str,
    whatsapp_attempt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mandatory SMS when WhatsApp cannot deliver (always used when SMS API is configured)."""
    if not is_configured():
        err = f"WhatsApp failed ({reason}) and SMS is not configured for fallback."
        if whatsapp_attempt:
            raise RuntimeError(err) from None
        raise RuntimeError(err)

    name = _recipient_name_for_demo(message, template_params)
    logger.info("WhatsApp unavailable (%s); mandatory SMS fallback to %s", reason, phone)
    result = await send_sms(phone, message, recipient_name=name)
    result["channel"] = "sms"
    result["delivery_mode"] = "whatsapp_sms_fallback"
    result["whatsapp_fallback_reason"] = reason
    if whatsapp_attempt:
        result["whatsapp_attempt"] = whatsapp_attempt
    if DEMO_SMS_MODE:
        result["demo_sms_body"] = format_demo_sms(name)
    return result


async def send_whatsapp(
    to: str,
    message: str,
    *,
    template_name: str = "",
    template_params: list[str] | None = None,
    event_type: str | None = None,
) -> dict[str, Any]:
    """PinBot v3 — template §8, text §1 (WhatsApp_API_Pinned_Documentation.pdf)."""
    from pinbot_whatsapp import send_template, send_text

    phone = normalize_phone(to)
    if not phone:
        return {"status": "skipped", "reason": "invalid_phone", "to": to}

    if not is_configured() and not whatsapp_configured():
        logger.info("[SpringEdge mock WhatsApp] %s: %s", phone, message[:120])
        return {"status": "mocked", "channel": "whatsapp", "to": phone, "message": message}

    if not whatsapp_configured():
        return await mandatory_sms_fallback(
            phone, message, template_params=template_params, reason="whatsapp_not_configured",
        )

    cfg = _pinbot_cfg()
    tname = (template_name or WHATSAPP_TEMPLATE).strip()
    params = list(template_params) if template_params else None
    safe_params = None
    if params:
        safe_params = [sanitize_template_text(p, max_len=200 if i == 0 else 450) for i, p in enumerate(params)]
    elif tname:
        safe_params = ["Franklin Wardcorpp Alert", sanitize_template_text(message)]

    # §8 template, or §1 plain text (TEXT_ONLY / fallback)
    if tname and not WHATSAPP_TEXT_ONLY:
        try:
            result = await send_template(
                phone,
                tname,
                safe_params or [],
                language=WHATSAPP_TEMPLATE_LANG or "en",
                event_type=event_type,
                **cfg,
            )
            result["message"] = message
            return result
        except Exception as e:
            if is_configured():
                return await mandatory_sms_fallback(
                    phone, message, template_params=safe_params or params,
                    reason=f"whatsapp_template_failed:{str(e)[:120]}",
                    whatsapp_attempt={"error": str(e)[:300], "template": tname},
                )
            if WHATSAPP_TEXT_FALLBACK and _is_template_send_error(e):
                logger.warning(
                    "PinBot template §8 failed (%s); using text §1 to %s",
                    str(e)[:160],
                    phone,
                )
                body = _whatsapp_text_from_template_params(safe_params or params, message)
                result = await send_text(phone, body, event_type=event_type, **cfg)
                result["delivery_mode"] = "pinbot_text_fallback"
                result["template"] = tname
                result["template_error"] = str(e)[:300]
                return result
            raise RuntimeError(_friendly_error(e)) from e

    body = _whatsapp_text_from_template_params(safe_params or params, message) if tname else sanitize_template_text(message, max_len=1000)
    try:
        result = await send_text(phone, body, event_type=event_type, **cfg)
        result["delivery_mode"] = "pinbot_text" if WHATSAPP_TEXT_ONLY else "pinbot_plain_text"
        if tname:
            result["template"] = tname
        return result
    except Exception as e:
        if is_configured():
            return await mandatory_sms_fallback(
                phone, message, template_params=safe_params or params,
                reason=f"whatsapp_text_failed:{str(e)[:120]}",
                whatsapp_attempt={"error": str(e)[:300]},
            )
        raise RuntimeError(_friendly_error(e)) from e


async def send_whatsapp_location(
    to: str,
    lat: float,
    lng: float,
    *,
    name: str = "",
    address: str = "",
    event_type: str | None = None,
) -> dict[str, Any]:
    """PinBot v3 §2 Send Location Message."""
    from pinbot_whatsapp import send_location

    phone = normalize_phone(to)
    if not phone:
        return {"status": "skipped", "reason": "invalid_phone", "to": to}

    loc_label = sanitize_template_text(name or "Agent", max_len=80)
    loc_area = sanitize_template_text(address or "", max_len=120)
    sms_body = f"Live location: {loc_label}"
    if loc_area:
        sms_body += f" ({loc_area})"
    sms_body += f". Lat {lat:.4f}, Lng {lng:.4f}."

    if not whatsapp_configured():
        return await mandatory_sms_fallback(
            phone, sms_body, reason="whatsapp_location_not_configured",
        )

    try:
        result = await send_location(
            phone, lat, lng,
            name=name, address=address, event_type=event_type,
            **_pinbot_cfg(),
        )
        if _whatsapp_delivery_failed(result):
            return await mandatory_sms_fallback(
                phone, sms_body, reason="whatsapp_location_delivery_failed",
                whatsapp_attempt=result,
            )
        return result
    except Exception as e:
        return await mandatory_sms_fallback(
            phone, sms_body, reason=f"whatsapp_location_failed:{str(e)[:120]}",
            whatsapp_attempt={"error": str(e)[:300]},
        )


async def pinbot_account_status() -> dict[str, Any] | None:
    """§26 Get user details — linked WABA numbers."""
    if not whatsapp_configured():
        return None
    try:
        from pinbot_whatsapp import fetch_user_details
        return await fetch_user_details(WHATSAPP_API_BASE, WABA_API_KEY)
    except Exception as e:
        logger.warning("PinBot getuserdetails failed: %s", e)
        return {"error": str(e)[:200]}


async def send_message(
    to: str,
    message: str,
    channel: str = "sms",
    *,
    template_name: str = "",
    template_params: list[str] | None = None,
    event_type: str | None = None,
) -> dict[str, Any]:
    ch = (channel or "sms").lower()
    if ch == "whatsapp":
        result = await send_whatsapp(
            to, message,
            template_name=template_name,
            template_params=template_params,
            event_type=event_type,
        )
        if _whatsapp_delivery_failed(result) and is_configured():
            return await mandatory_sms_fallback(
                normalize_phone(to) or to,
                message,
                template_params=template_params,
                reason="whatsapp_delivery_failed",
                whatsapp_attempt=result,
            )
        return result
    return await send_sms(to, message)

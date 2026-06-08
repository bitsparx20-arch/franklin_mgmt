"""WhatsApp alerts to CEO(s) via the shared lms_notification template."""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Awaitable

logger = logging.getLogger("ceo_notify")


def whatsapp_template_name() -> str:
    return (os.environ.get("SPRINGEDGE_WHATSAPP_TEMPLATE") or "lms_notification").strip()


def whatsapp_template_params(alert: str, body: str) -> list[str]:
    """lms_notification: {{1}} = Notification Alert, {{2}} = Msg body."""
    from springedge import sanitize_template_text

    return [
        sanitize_template_text(alert, max_len=200),
        sanitize_template_text(body, max_len=450),
    ]


async def ceo_phones(db) -> list[str]:
    """Resolve CEO WhatsApp numbers: env override, then CEO users in DB."""
    from springedge import normalize_phone

    override = (os.environ.get("SPRINGEDGE_CEO_PHONES") or "").strip()
    if override:
        phones: list[str] = []
        seen: set[str] = set()
        for raw in override.split(","):
            phone = normalize_phone(raw.strip())
            if phone and phone not in seen:
                seen.add(phone)
                phones.append(phone)
        return phones

    phones: list[str] = []
    async for u in db.users.find({"role": "ceo"}, {"phone": 1, "_id": 0}):
        phone = normalize_phone((u.get("phone") or "").strip())
        if phone and phone not in phones:
            phones.append(phone)

    fallback = normalize_phone((os.environ.get("SPRINGEDGE_TEST_PHONE") or "").strip())
    if not phones and fallback:
        phones.append(fallback)
    return phones


async def notify_ceos_whatsapp(
    db,
    send_fn: Callable[..., Awaitable[dict]],
    *,
    alert: str,
    message: str,
    event_type: str,
    triggered_by: str | None = None,
) -> list[dict[str, Any]]:
    """
    Send lms_notification template WhatsApp to all configured CEOs.
    send_fn should be springedge_send from server.py.
    """
    phones = await ceo_phones(db)
    if not phones:
        logger.warning("CEO WhatsApp skipped — no phone numbers (set SPRINGEDGE_CEO_PHONES or CEO user phones)")
        return []

    tmpl = whatsapp_template_name()
    params = whatsapp_template_params(alert, message)
    results: list[dict[str, Any]] = []

    for phone in phones:
        try:
            result = await send_fn(
                phone,
                message,
                "whatsapp",
                template_name=tmpl,
                template_params=params,
                user_id=triggered_by,
                recipient_label=f"CEO · {event_type}",
                event_type=event_type,
            )
            results.append({"phone": phone, **result})
        except Exception as e:
            logger.exception("CEO WhatsApp failed for %s", phone)
            results.append({"phone": phone, "status": "failed", "error": str(e)})
    return results

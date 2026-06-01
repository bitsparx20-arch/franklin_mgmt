"""Route Franklin-AI requests to AWS Bedrock or Emergent (legacy)."""
from __future__ import annotations

import os
from typing import Any

from bedrock_llm import complete_chat as bedrock_complete
from bedrock_llm import is_configured as bedrock_configured
from bedrock_llm import status as bedrock_status


def _provider() -> str:
    explicit = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if explicit in ("bedrock", "emergent"):
        return explicit
    if bedrock_configured():
        return "bedrock"
    if os.environ.get("EMERGENT_LLM_KEY", "").strip():
        return "emergent"
    return ""


def is_configured() -> bool:
    p = _provider()
    if p == "bedrock":
        return bedrock_configured()
    if p == "emergent":
        return bool(os.environ.get("EMERGENT_LLM_KEY", "").strip())
    return False


def status() -> dict[str, Any]:
    p = _provider() or "none"
    if p == "bedrock":
        return bedrock_status()
    if p == "emergent":
        return {"provider": "emergent", "configured": bool(os.environ.get("EMERGENT_LLM_KEY"))}
    return {
        "provider": "none",
        "configured": False,
        "hint": "Set LLM_PROVIDER=bedrock and BEDROCK_MODEL_ID, or EMERGENT_LLM_KEY",
    }


async def complete_chat(system: str, prior: list[dict], user_message: str) -> str:
    p = _provider()
    if p == "bedrock":
        return await bedrock_complete(system, prior, user_message)
    if p == "emergent":
        return await _emergent_complete(system, prior, user_message)
    raise RuntimeError(
        "LLM not configured. Set LLM_PROVIDER=bedrock with BEDROCK_MODEL_ID and AWS credentials, "
        "or EMERGENT_LLM_KEY for Emergent."
    )


async def _emergent_complete(system: str, prior: list[dict], user_message: str) -> str:
    api_key = os.environ.get("EMERGENT_LLM_KEY", "").strip()
    if not api_key:
        raise RuntimeError("EMERGENT_LLM_KEY is not set")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:
        raise RuntimeError(f"Emergent LLM library unavailable: {e}") from e

    session_id = "franklin-emergent"
    chat = LlmChat(api_key=api_key, session_id=session_id, system_message=system).with_model(
        "anthropic", "claude-sonnet-4-5-20250929"
    )
    for m in prior:
        if m.get("role") == "user":
            try:
                await chat.send_message(UserMessage(text=m["text"]))
            except Exception:
                pass
    reply = await chat.send_message(UserMessage(text=user_message))
    return str(reply)

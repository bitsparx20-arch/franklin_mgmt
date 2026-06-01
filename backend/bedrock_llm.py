"""AWS Bedrock chat completion for Franklin-AI."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("bedrock")

def _model_id() -> str:
    _reload_env()
    return os.environ.get("BEDROCK_MODEL_ID", "").strip()


def _region() -> str:
    _reload_env()
    return os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")).strip()


def _max_tokens() -> int:
    return int(os.environ.get("BEDROCK_MAX_TOKENS", "2048"))


def _temperature() -> float:
    return float(os.environ.get("BEDROCK_TEMPERATURE", "0.3"))


def _reload_env() -> None:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).parent / ".env", override=True)


def _bedrock_api_key() -> str:
    """Long/short-term Bedrock API key from console (Discover → API keys)."""
    _reload_env()
    return (os.environ.get("BEDROCK_API_KEY") or os.environ.get("AWS_BEARER_TOKEN_BEDROCK") or "").strip()


def _has_bedrock_api_key() -> bool:
    return bool(_bedrock_api_key())


def _has_explicit_aws_keys() -> bool:
    return bool(os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"))


def is_configured() -> bool:
    if not _model_id():
        return False
    return _has_bedrock_api_key() or _has_explicit_aws_keys()


def _apply_bearer_token() -> None:
    """boto3 reads AWS_BEARER_TOKEN_BEDROCK for Bedrock API key auth."""
    key = _bedrock_api_key()
    if key:
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = key


def _auth_mode() -> str:
    if _has_bedrock_api_key():
        return "bedrock_api_key"
    if _has_explicit_aws_keys():
        return "iam_access_keys"
    return "default_chain"


def _get_client():
    _apply_bearer_token()
    kwargs: dict[str, Any] = {"region_name": _region()}
    # IAM keys are ignored when bearer token is set (Bedrock API key takes precedence)
    if not _has_bedrock_api_key() and _has_explicit_aws_keys():
        kwargs["aws_access_key_id"] = os.environ["AWS_ACCESS_KEY_ID"]
        kwargs["aws_secret_access_key"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        token = os.environ.get("AWS_SESSION_TOKEN")
        if token:
            kwargs["aws_session_token"] = token
    return boto3.client("bedrock-runtime", **kwargs)


def _friendly_error(exc: Exception) -> str:
    msg = str(exc)
    if "INVALID_PAYMENT_INSTRUMENT" in msg or "payment instrument" in msg.lower():
        if "anthropic" in _model_id().lower() or "marketplace" in msg.lower():
            return (
                "Claude models use AWS Marketplace and usually require a credit or debit card "
                "(UPI AutoPay often is not enough). Add a card under Billing → Payment preferences, "
                "enable the model in Bedrock → Model access, or set BEDROCK_MODEL_ID=apac.amazon.nova-micro-v1:0 "
                "for Amazon Nova (works with your current billing)."
            )
        return (
            "AWS Bedrock billing is not active for this model yet. "
            "Check Payment preferences and Model access in the Bedrock console, wait a few minutes, then retry."
        )
    if "AccessDeniedException" in msg or "not authorized" in msg.lower():
        return (
            "AWS denied Bedrock access. Enable the model under Model access, "
            "or check that your API key has permission to call this model."
        )
    if "inference profile" in msg.lower():
        return (
            f"Use an inference profile ID, not the raw model ID. "
            f"For Claude Sonnet 4 try: global.anthropic.claude-sonnet-4-6"
        )
    if "ResourceNotFoundException" in msg or "model identifier" in msg.lower():
        return f"Bedrock model not found: {_model_id()}. Check BEDROCK_MODEL_ID and region {_region()}."
    if "ExpiredToken" in msg or "InvalidClientTokenId" in msg or "UnauthorizedException" in msg:
        return "Bedrock API key or AWS credentials are invalid or expired. Generate a new key in Bedrock → API keys."
    if "ThrottlingException" in msg:
        return "Bedrock rate limit hit. Wait a moment and retry."
    return msg[:400]


def _converse_sync(system: str, prior: list[dict], user_message: str) -> str:
    model_id = _model_id()
    if not model_id:
        raise RuntimeError("BEDROCK_MODEL_ID is not set")
    if not is_configured():
        raise RuntimeError(
            "Set BEDROCK_API_KEY (long-term key from Bedrock console) or AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY"
        )

    client = _get_client()
    messages: list[dict] = []
    for m in prior:
        role = m.get("role")
        text = (m.get("text") or "").strip()
        if role not in ("user", "assistant") or not text:
            continue
        messages.append({"role": role, "content": [{"text": text}]})
    messages.append({"role": "user", "content": [{"text": user_message}]})

    response = client.converse(
        modelId=model_id,
        system=[{"text": system}],
        messages=messages,
        inferenceConfig={
            "maxTokens": _max_tokens(),
            "temperature": _temperature(),
        },
    )

    output = response.get("output", {}).get("message", {})
    parts = output.get("content") or []
    texts = [p.get("text", "") for p in parts if p.get("text")]
    reply = "\n".join(texts).strip()
    if not reply:
        raise RuntimeError("Bedrock returned an empty response")
    return reply


async def complete_chat(system: str, prior: list[dict], user_message: str) -> str:
    try:
        return await asyncio.to_thread(_converse_sync, system, prior, user_message)
    except (ClientError, BotoCoreError) as e:
        logger.exception("Bedrock API error")
        raise RuntimeError(_friendly_error(e)) from e
    except Exception as e:
        logger.exception("Bedrock error")
        raise RuntimeError(_friendly_error(e)) from e


def status() -> dict[str, Any]:
    return {
        "provider": "bedrock",
        "configured": is_configured(),
        "model_id": _model_id() or None,
        "region": _region(),
        "auth_mode": _auth_mode(),
        "has_api_key": _has_bedrock_api_key(),
    }

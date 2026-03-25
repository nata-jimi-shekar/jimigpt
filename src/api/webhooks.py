"""Twilio webhook handler.

Receives delivery status callbacks from Twilio for both SMS and WhatsApp,
records them in the in-memory status store, and detects the channel from
the `From` field (WhatsApp callbacks carry a "whatsapp:" prefix).

Phase 5 (F05) will replace the in-memory store with Supabase.

Twilio requirement: always return 2xx — any non-2xx triggers automatic retry.
"""

from __future__ import annotations

from typing import TypedDict

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request
from twilio.request_validator import RequestValidator  # type: ignore[import-untyped]

from src.shared.config import Settings

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

_settings = Settings()

# ---------------------------------------------------------------------------
# Status classification
# ---------------------------------------------------------------------------

TERMINAL_SUCCESS_STATUSES: frozenset[str] = frozenset({"delivered"})
TERMINAL_FAILURE_STATUSES: frozenset[str] = frozenset({"failed", "undelivered"})

# ---------------------------------------------------------------------------
# In-memory status store (Phase 1 — replaced by DB query in F05)
# Maps Twilio MessageSid → {status, channel}.
# ---------------------------------------------------------------------------


class _StatusRecord(TypedDict):
    status: str
    channel: str  # "sms" | "whatsapp"


_status_store: dict[str, _StatusRecord] = {}


def _detect_channel(from_field: str | None) -> str:
    """Infer delivery channel from the Twilio `From` field.

    WhatsApp callbacks carry a "whatsapp:" prefix on the sender number.
    Everything else is treated as SMS.
    """
    if from_field and from_field.startswith("whatsapp:"):
        return "whatsapp"
    return "sms"


def get_delivery_status(message_sid: str) -> str | None:
    """Return the latest known delivery status for a Twilio MessageSid."""
    record = _status_store.get(message_sid)
    return record["status"] if record else None


def get_delivery_channel(message_sid: str) -> str | None:
    """Return the detected delivery channel ('sms' or 'whatsapp') for a SID."""
    record = _status_store.get(message_sid)
    return record["channel"] if record else None


def reset_status_store() -> None:
    """Clear the status store — used in test teardown."""
    _status_store.clear()


# ---------------------------------------------------------------------------
# Signature verification dependency
# ---------------------------------------------------------------------------


async def verify_twilio_signature(
    request: Request,
    x_twilio_signature: str = Header(...),
) -> None:
    """FastAPI dependency: validates the X-Twilio-Signature header.

    Raises HTTP 403 if the signature is invalid.
    Override this dependency in tests to bypass validation.
    """
    validator = RequestValidator(_settings.twilio_auth_token)
    form_data = await request.form()
    params = dict(form_data)
    url = str(request.url)

    if not validator.validate(url, params, x_twilio_signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/twilio")
async def twilio_status_callback(
    message_sid: str = Form(..., alias="MessageSid"),
    message_status: str = Form(..., alias="MessageStatus"),
    from_number: str | None = Form(None, alias="From"),
    _sig: None = Depends(verify_twilio_signature),
) -> dict[str, str]:
    """Receive a Twilio delivery status callback (SMS or WhatsApp).

    Twilio POSTs here whenever a message status changes. The `From` field
    identifies the channel: WhatsApp senders carry a "whatsapp:" prefix.

    Always returns 200 so Twilio does not retry.
    """
    channel = _detect_channel(from_number)
    _status_store[message_sid] = _StatusRecord(status=message_status, channel=channel)
    return {
        "status": "ok",
        "message_sid": message_sid,
        "recorded_status": message_status,
        "channel": channel,
    }

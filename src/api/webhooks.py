"""Twilio webhook handler.

Receives delivery status callbacks from Twilio and records them in the
in-memory status store. Phase 5 (F05) will replace the store with Supabase.

Twilio requirement: always return 2xx — any non-2xx triggers automatic retry.
"""

from __future__ import annotations

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
# Maps Twilio MessageSid → latest MessageStatus string.
# ---------------------------------------------------------------------------

_status_store: dict[str, str] = {}


def get_delivery_status(message_sid: str) -> str | None:
    """Return the latest known delivery status for a Twilio MessageSid."""
    return _status_store.get(message_sid)


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
    _sig: None = Depends(verify_twilio_signature),
) -> dict[str, str]:
    """Receive a Twilio delivery status callback.

    Twilio POSTs here whenever a message status changes (sent, delivered,
    failed, undelivered). We record the latest status and always return 200
    so Twilio does not retry.
    """
    _status_store[message_sid] = message_status
    return {"status": "ok", "message_sid": message_sid, "recorded_status": message_status}

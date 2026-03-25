"""Twilio SMS delivery client.

Wraps the Twilio REST client with error handling and returns a DeliveryResult.
All external SMS sends go through send_sms() — never call Twilio directly.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from twilio.base.exceptions import TwilioRestException  # type: ignore[import-untyped]
from twilio.rest import Client  # type: ignore[import-untyped]

from src.delivery.models import DeliveryChannel, DeliveryResult
from src.shared.config import Settings

# E.164 format: optional + then 7–15 digits
_E164_RE = re.compile(r"^\+?[1-9]\d{6,14}$")

_settings = Settings()


def _twilio_client() -> Client:
    return Client(_settings.twilio_account_sid, _settings.twilio_auth_token)


def send_sms(to: str, body: str) -> DeliveryResult:
    """Send an SMS via Twilio and return a DeliveryResult.

    Validates inputs, calls Twilio, and maps success/failure to DeliveryResult.
    Never raises — all errors are captured in DeliveryResult.error.
    """
    if not to or not _E164_RE.match(to):
        raise ValueError(f"Invalid phone number: {to!r}. Must be E.164 format.")
    if not body:
        raise ValueError("Message body must not be empty.")

    try:
        client = _twilio_client()
        message = client.messages.create(
            to=to,
            from_=_settings.twilio_phone_number,
            body=body,
        )
        return DeliveryResult(
            success=True,
            channel=DeliveryChannel.SMS,
            delivered_at=datetime.now(tz=UTC),
            external_id=message.sid,
            error=None,
        )
    except TwilioRestException as exc:
        return DeliveryResult(
            success=False,
            channel=DeliveryChannel.SMS,
            delivered_at=None,
            external_id=None,
            error=str(exc),
        )
    except Exception as exc:  # noqa: BLE001
        return DeliveryResult(
            success=False,
            channel=DeliveryChannel.SMS,
            delivered_at=None,
            external_id=None,
            error=f"Unexpected error: {exc}",
        )

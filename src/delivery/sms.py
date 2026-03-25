"""Twilio SMS delivery client.

Wraps the Twilio REST client with error handling and returns a DeliveryResult.
All external SMS sends go through send_sms() — never call Twilio directly.
For reliable delivery, use deliver_with_retry() which adds exponential backoff.
"""

from __future__ import annotations

import re
import time as _time
from collections.abc import Callable
from datetime import UTC, datetime

from twilio.base.exceptions import TwilioRestException  # type: ignore[import-untyped]
from twilio.rest import Client  # type: ignore[import-untyped]

from src.delivery.models import DeliveryChannel, DeliveryRequest, DeliveryResult
from src.shared.config import Settings

# ---------------------------------------------------------------------------
# Retry constants
# ---------------------------------------------------------------------------

MAX_ATTEMPTS = 3
# Seconds to wait before each retry: 1 min, 5 min, 15 min
RETRY_DELAYS: tuple[int, int, int] = (60, 300, 900)

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


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------

_SendFn = Callable[[str, str], DeliveryResult]
_SleepFn = Callable[[float], None]


def deliver_with_retry(
    request: DeliveryRequest,
    *,
    _send_fn: _SendFn = send_sms,
    _sleep_fn: _SleepFn = _time.sleep,
) -> DeliveryResult:
    """Deliver an SMS with exponential backoff retry (up to MAX_ATTEMPTS).

    Attempts:  1 (immediate) → sleep delay[0] → 2 → sleep delay[1] → 3
    Delays:    60 s, 300 s  (15 min delay is defined but unused at 3 attempts)

    ``_send_fn`` and ``_sleep_fn`` are injectable for testing — pass no-op
    lambdas to skip real network calls and real sleeps in unit tests.

    Raises:
        ValueError: if ``request.recipient_phone`` is missing or invalid
                    (raised immediately, before any attempt).
    """
    phone = request.recipient_phone
    if not phone:
        raise ValueError("DeliveryRequest.recipient_phone is required for SMS delivery.")

    body = request.message.content
    last_result: DeliveryResult | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        now = datetime.now(tz=UTC)
        result = _send_fn(phone, body)
        last_result = result.model_copy(
            update={"attempts": attempt, "last_attempt_at": now}
        )

        if last_result.success:
            return last_result

        # Sleep before retry — but not after the final attempt
        if attempt < MAX_ATTEMPTS:
            _sleep_fn(RETRY_DELAYS[attempt - 1])

    # All attempts exhausted — return the last failure result
    assert last_result is not None  # always set after ≥1 loop iteration
    return last_result

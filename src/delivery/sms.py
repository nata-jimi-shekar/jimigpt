"""Twilio delivery client — SMS and WhatsApp.

All outbound messages go through send_sms(), send_whatsapp(), or the unified
send_message() router. For reliable delivery use deliver_with_retry(), which
adds exponential backoff and auto-selects the channel from the DeliveryRequest.
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


def _validate_inputs(to: str, body: str) -> None:
    if not to or not _E164_RE.match(to):
        raise ValueError(f"Invalid phone number: {to!r}. Must be E.164 format.")
    if not body:
        raise ValueError("Message body must not be empty.")


# ---------------------------------------------------------------------------
# SMS
# ---------------------------------------------------------------------------


def send_sms(to: str, body: str) -> DeliveryResult:
    """Send an SMS via Twilio and return a DeliveryResult.

    Never raises — all errors are captured in DeliveryResult.error.
    """
    _validate_inputs(to, body)
    try:
        message = _twilio_client().messages.create(
            to=to,
            from_=_settings.twilio_phone_number,
            body=body,
        )
        return DeliveryResult(
            success=True,
            channel=DeliveryChannel.SMS,
            delivered_at=datetime.now(tz=UTC),
            external_id=message.sid,
        )
    except TwilioRestException as exc:
        return DeliveryResult(
            success=False, channel=DeliveryChannel.SMS, error=str(exc)
        )
    except Exception as exc:  # noqa: BLE001
        return DeliveryResult(
            success=False, channel=DeliveryChannel.SMS,
            error=f"Unexpected error: {exc}",
        )


# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------


def send_whatsapp(to: str, body: str) -> DeliveryResult:
    """Send a WhatsApp message via Twilio.

    Same Twilio API as SMS — only the 'whatsapp:' prefix on to/from differs.
    Never raises — all errors are captured in DeliveryResult.error.
    """
    _validate_inputs(to, body)
    try:
        message = _twilio_client().messages.create(
            to=f"whatsapp:{to}",
            from_=f"whatsapp:{_settings.twilio_whatsapp_from}",
            body=body,
        )
        return DeliveryResult(
            success=True,
            channel=DeliveryChannel.WHATSAPP,
            delivered_at=datetime.now(tz=UTC),
            external_id=message.sid,
        )
    except TwilioRestException as exc:
        return DeliveryResult(
            success=False, channel=DeliveryChannel.WHATSAPP, error=str(exc)
        )
    except Exception as exc:  # noqa: BLE001
        return DeliveryResult(
            success=False, channel=DeliveryChannel.WHATSAPP,
            error=f"Unexpected error: {exc}",
        )


# ---------------------------------------------------------------------------
# Unified channel router
# ---------------------------------------------------------------------------


def send_message(to: str, body: str, channel: DeliveryChannel) -> DeliveryResult:
    """Route a message to the correct channel sender."""
    match channel:
        case DeliveryChannel.SMS:
            return send_sms(to, body)
        case DeliveryChannel.WHATSAPP:
            return send_whatsapp(to, body)
        case _:
            raise ValueError(f"Unsupported delivery channel: {channel}")


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------

_SendFn = Callable[[str, str], DeliveryResult]
_SleepFn = Callable[[float], None]


def deliver_with_retry(
    request: DeliveryRequest,
    *,
    _send_fn: _SendFn | None = None,  # None = auto-select by channel
    _sleep_fn: _SleepFn = _time.sleep,
) -> DeliveryResult:
    """Deliver a message with exponential backoff retry (up to MAX_ATTEMPTS).

    Attempts:  1 (immediate) → sleep delay[0] → 2 → sleep delay[1] → 3
    Delays:    60 s, 300 s  (15 min slot defined but unused at 3 attempts)

    When ``_send_fn`` is None the channel is read from ``request.channel``
    and the appropriate sender (send_sms / send_whatsapp) is selected
    automatically. Passing an explicit ``_send_fn`` overrides this — all
    existing tests that inject their own function continue to work unchanged.

    Raises:
        ValueError: if ``request.recipient_phone`` is missing
                    (raised immediately, before any attempt).
    """
    phone = request.recipient_phone
    if not phone:
        raise ValueError("DeliveryRequest.recipient_phone is required for delivery.")

    effective_send: _SendFn
    if _send_fn is not None:
        effective_send = _send_fn
    else:
        effective_send = lambda to, body: send_message(to, body, request.channel)  # noqa: E731

    body = request.message.content
    last_result: DeliveryResult | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        now = datetime.now(tz=UTC)
        result = effective_send(phone, body)
        last_result = result.model_copy(
            update={"attempts": attempt, "last_attempt_at": now}
        )

        if last_result.success:
            return last_result

        if attempt < MAX_ATTEMPTS:
            _sleep_fn(RETRY_DELAYS[attempt - 1])

    assert last_result is not None
    return last_result

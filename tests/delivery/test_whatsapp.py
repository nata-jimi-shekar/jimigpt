"""Tests for WhatsApp channel and unified send_message() router — TDD."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from twilio.base.exceptions import TwilioRestException

from src.delivery.models import DeliveryChannel, DeliveryRequest, DeliveryResult
from src.delivery.sms import deliver_with_retry, send_message, send_whatsapp
from src.messaging.generator import GeneratedMessage
from src.messaging.models import MessageIntent
from src.personality.models import ToneSpectrum

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tone() -> ToneSpectrum:
    return ToneSpectrum(
        warmth=0.7, humor=0.4, directness=0.5,
        gravity=0.2, energy=0.6, vulnerability=0.3,
    )


def _msg() -> GeneratedMessage:
    return GeneratedMessage(
        message_id="msg-001",
        entity_id="entity-abc",
        content="Hey! Thinking of you 🐾",
        generated_at=datetime.now(tz=UTC),
        model_used="claude-sonnet-4-6",
        prompt_tokens=50,
        completion_tokens=20,
        message_category="greeting",
        intended_intent=MessageIntent.AFFIRM,
        intended_tone=_tone(),
        character_count=22,
    )


_NO_SLEEP = lambda _: None  # noqa: E731


# ---------------------------------------------------------------------------
# send_whatsapp — successful delivery
# ---------------------------------------------------------------------------


@patch("src.delivery.sms.Client")
def test_send_whatsapp_success_returns_delivery_result(
    mock_client_cls: MagicMock,
) -> None:
    """Successful send returns DeliveryResult with success=True and WHATSAPP channel."""
    mock_message = MagicMock()
    mock_message.sid = "WA_abc123"
    mock_client_cls.return_value.messages.create.return_value = mock_message

    result = send_whatsapp(to="+573001234567", body="Hola!")

    assert result.success is True
    assert result.channel == DeliveryChannel.WHATSAPP
    assert result.external_id == "WA_abc123"
    assert result.error is None
    assert result.delivered_at is not None


@patch("src.delivery.sms.Client")
def test_send_whatsapp_prefixes_to_number(mock_client_cls: MagicMock) -> None:
    """to number gets 'whatsapp:' prefix when calling Twilio."""
    mock_message = MagicMock()
    mock_message.sid = "WA_prefix"
    mock_client_cls.return_value.messages.create.return_value = mock_message

    send_whatsapp(to="+573001234567", body="Test")

    call_kwargs = mock_client_cls.return_value.messages.create.call_args.kwargs
    assert call_kwargs["to"] == "whatsapp:+573001234567"


@patch("src.delivery.sms.Client")
def test_send_whatsapp_prefixes_from_number(mock_client_cls: MagicMock) -> None:
    """from_ uses twilio_whatsapp_from setting with 'whatsapp:' prefix."""
    mock_message = MagicMock()
    mock_message.sid = "WA_from"
    mock_client_cls.return_value.messages.create.return_value = mock_message

    send_whatsapp(to="+573001234567", body="Test")

    call_kwargs = mock_client_cls.return_value.messages.create.call_args.kwargs
    assert call_kwargs["from_"].startswith("whatsapp:")


@patch("src.delivery.sms.Client")
def test_send_whatsapp_twilio_error_returns_failure(
    mock_client_cls: MagicMock,
) -> None:
    """TwilioRestException is caught and returned as failure DeliveryResult."""
    mock_client_cls.return_value.messages.create.side_effect = TwilioRestException(
        status=400, uri="/Messages", msg="WhatsApp number not opted in"
    )

    result = send_whatsapp(to="+573001234567", body="Test")

    assert result.success is False
    assert result.channel == DeliveryChannel.WHATSAPP
    assert result.error is not None
    assert "WhatsApp number not opted in" in result.error
    assert result.external_id is None


@patch("src.delivery.sms.Client")
def test_send_whatsapp_unexpected_error_returns_failure(
    mock_client_cls: MagicMock,
) -> None:
    mock_client_cls.return_value.messages.create.side_effect = RuntimeError("timeout")

    result = send_whatsapp(to="+573001234567", body="Test")

    assert result.success is False
    assert result.channel == DeliveryChannel.WHATSAPP


# ---------------------------------------------------------------------------
# send_whatsapp — validation (same rules as send_sms)
# ---------------------------------------------------------------------------


def test_send_whatsapp_rejects_invalid_phone() -> None:
    with pytest.raises(ValueError, match="phone"):
        send_whatsapp(to="not-a-number", body="Hi")


def test_send_whatsapp_rejects_empty_phone() -> None:
    with pytest.raises(ValueError, match="phone"):
        send_whatsapp(to="", body="Hi")


def test_send_whatsapp_rejects_empty_body() -> None:
    with pytest.raises(ValueError, match="body"):
        send_whatsapp(to="+573001234567", body="")


# ---------------------------------------------------------------------------
# send_message — channel router
# ---------------------------------------------------------------------------


@patch("src.delivery.sms.send_sms")
def test_send_message_routes_sms(mock_send_sms: MagicMock) -> None:
    """send_message with SMS channel delegates to send_sms."""
    mock_send_sms.return_value = DeliveryResult(
        success=True, channel=DeliveryChannel.SMS
    )

    result = send_message(to="+15551234567", body="Hi", channel=DeliveryChannel.SMS)

    mock_send_sms.assert_called_once_with("+15551234567", "Hi")
    assert result.channel == DeliveryChannel.SMS


@patch("src.delivery.sms.send_whatsapp")
def test_send_message_routes_whatsapp(mock_send_whatsapp: MagicMock) -> None:
    """send_message with WHATSAPP channel delegates to send_whatsapp."""
    mock_send_whatsapp.return_value = DeliveryResult(
        success=True, channel=DeliveryChannel.WHATSAPP
    )

    result = send_message(
        to="+573001234567", body="Hola", channel=DeliveryChannel.WHATSAPP
    )

    mock_send_whatsapp.assert_called_once_with("+573001234567", "Hola")
    assert result.channel == DeliveryChannel.WHATSAPP


def test_send_message_unsupported_channel_raises() -> None:
    """Unsupported channels (VOICE, PUSH) raise ValueError."""
    with pytest.raises(ValueError, match="Unsupported"):
        send_message(to="+15551234567", body="Hi", channel=DeliveryChannel.VOICE)

    with pytest.raises(ValueError, match="Unsupported"):
        send_message(to="+15551234567", body="Hi", channel=DeliveryChannel.PUSH)


# ---------------------------------------------------------------------------
# deliver_with_retry — channel auto-selection
# ---------------------------------------------------------------------------


def test_deliver_with_retry_auto_selects_sms_channel() -> None:
    """deliver_with_retry with no _send_fn uses SMS sender for SMS request."""
    sms_called_with: list[tuple[str, str]] = []

    def fake_sms(to: str, body: str) -> DeliveryResult:
        sms_called_with.append((to, body))
        return DeliveryResult(
            success=True, channel=DeliveryChannel.SMS,
            delivered_at=datetime.now(tz=UTC), external_id="SM_auto",
        )

    request = DeliveryRequest(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        recipient_phone="+15551234567",
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id="user-001",
    )

    with patch("src.delivery.sms.send_sms", side_effect=fake_sms):
        result = deliver_with_retry(request, _sleep_fn=_NO_SLEEP)

    assert result.success is True
    assert result.channel == DeliveryChannel.SMS


def test_deliver_with_retry_auto_selects_whatsapp_channel() -> None:
    """deliver_with_retry with no _send_fn uses WhatsApp sender for WhatsApp request."""
    whatsapp_called = False

    def fake_whatsapp(to: str, body: str) -> DeliveryResult:
        nonlocal whatsapp_called
        whatsapp_called = True
        return DeliveryResult(
            success=True, channel=DeliveryChannel.WHATSAPP,
            delivered_at=datetime.now(tz=UTC), external_id="WA_auto",
        )

    request = DeliveryRequest(
        message=_msg(),
        channel=DeliveryChannel.WHATSAPP,
        recipient_phone="+573001234567",
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id="user-001",
    )

    with patch("src.delivery.sms.send_whatsapp", side_effect=fake_whatsapp):
        result = deliver_with_retry(request, _sleep_fn=_NO_SLEEP)

    assert whatsapp_called is True
    assert result.success is True


def test_deliver_with_retry_explicit_send_fn_overrides_channel() -> None:
    """Explicit _send_fn always wins — existing tests continue to work."""
    custom_called = False

    def custom_fn(to: str, body: str) -> DeliveryResult:
        nonlocal custom_called
        custom_called = True
        return DeliveryResult(
            success=True, channel=DeliveryChannel.SMS,
            delivered_at=datetime.now(tz=UTC), external_id="SM_custom",
        )

    request = DeliveryRequest(
        message=_msg(),
        channel=DeliveryChannel.WHATSAPP,  # would normally use WA
        recipient_phone="+573001234567",
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id="user-001",
    )

    result = deliver_with_retry(request, _send_fn=custom_fn, _sleep_fn=_NO_SLEEP)

    assert custom_called is True
    assert result.success is True


# ---------------------------------------------------------------------------
# Settings — TWILIO_WHATSAPP_FROM
# ---------------------------------------------------------------------------


def test_settings_has_twilio_whatsapp_from(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings exposes TWILIO_WHATSAPP_FROM env var."""
    monkeypatch.setenv("TWILIO_WHATSAPP_FROM", "+14155238886")
    from src.shared.config import Settings

    s = Settings()
    assert s.twilio_whatsapp_from == "+14155238886"


def test_settings_twilio_whatsapp_from_defaults_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TWILIO_WHATSAPP_FROM", raising=False)
    from src.shared.config import Settings

    s = Settings()
    assert s.twilio_whatsapp_from == ""

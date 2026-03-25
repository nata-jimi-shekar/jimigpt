"""Tests for Twilio SMS client — TDD: tests written before implementation."""

from unittest.mock import MagicMock, patch

import pytest
from twilio.base.exceptions import TwilioRestException

from src.delivery.models import DeliveryChannel, DeliveryResult
from src.delivery.sms import send_sms
from src.shared.config import Settings

# ---------------------------------------------------------------------------
# Settings tests
# ---------------------------------------------------------------------------


def test_settings_reads_twilio_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings loads Twilio credentials from environment variables."""
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACtest123")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token456")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15550001111")

    s = Settings()
    assert s.twilio_account_sid == "ACtest123"
    assert s.twilio_auth_token == "token456"
    assert s.twilio_phone_number == "+15550001111"


def test_settings_has_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings exposes ANTHROPIC_API_KEY."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    s = Settings()
    assert s.anthropic_api_key == "sk-ant-test"


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings provides sensible defaults for optional fields."""
    # Clear optional env vars to test defaults
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    s = Settings()
    assert s.environment == "development"
    assert s.openai_api_key is None


# ---------------------------------------------------------------------------
# send_sms — successful delivery
# ---------------------------------------------------------------------------


@patch("src.delivery.sms.Client")
def test_send_sms_success_returns_delivery_result(mock_client_cls: MagicMock) -> None:
    """Successful Twilio send returns DeliveryResult with success=True and SID."""
    mock_message = MagicMock()
    mock_message.sid = "SM1234567890abcdef"
    mock_client_cls.return_value.messages.create.return_value = mock_message

    result = send_sms(to="+15551234567", body="Hey there!")

    assert isinstance(result, DeliveryResult)
    assert result.success is True
    assert result.external_id == "SM1234567890abcdef"
    assert result.error is None
    assert result.channel == DeliveryChannel.SMS
    assert result.delivered_at is not None


@patch("src.delivery.sms.Client")
def test_send_sms_calls_twilio_with_correct_args(mock_client_cls: MagicMock) -> None:
    """send_sms passes to, body, and from_ to Twilio messages.create."""
    mock_message = MagicMock()
    mock_message.sid = "SMabc"
    mock_client_cls.return_value.messages.create.return_value = mock_message

    send_sms(to="+15559876543", body="Hello from Jimi!")

    mock_client_cls.return_value.messages.create.assert_called_once()
    call_kwargs = mock_client_cls.return_value.messages.create.call_args.kwargs
    assert call_kwargs["to"] == "+15559876543"
    assert call_kwargs["body"] == "Hello from Jimi!"
    assert "from_" in call_kwargs


# ---------------------------------------------------------------------------
# send_sms — Twilio errors
# ---------------------------------------------------------------------------


@patch("src.delivery.sms.Client")
def test_send_sms_twilio_error_returns_failure(mock_client_cls: MagicMock) -> None:
    """TwilioRestException is caught and returned as DeliveryResult with success=False."""
    mock_client_cls.return_value.messages.create.side_effect = TwilioRestException(
        status=400,
        uri="/Messages",
        msg="Invalid phone number",
    )

    result = send_sms(to="+15551234567", body="Test")

    assert result.success is False
    assert result.error is not None
    assert "Invalid phone number" in result.error
    assert result.external_id is None
    assert result.delivered_at is None
    assert result.channel == DeliveryChannel.SMS


@patch("src.delivery.sms.Client")
def test_send_sms_unexpected_error_returns_failure(mock_client_cls: MagicMock) -> None:
    """Unexpected exceptions are caught and returned as failure DeliveryResult."""
    mock_client_cls.return_value.messages.create.side_effect = RuntimeError(
        "Network timeout"
    )

    result = send_sms(to="+15551234567", body="Test")

    assert result.success is False
    assert result.error is not None
    assert result.delivered_at is None


# ---------------------------------------------------------------------------
# Phone number validation
# ---------------------------------------------------------------------------


def test_send_sms_rejects_invalid_phone_number() -> None:
    """send_sms raises ValueError for obviously invalid phone numbers."""
    with pytest.raises(ValueError, match="phone"):
        send_sms(to="not-a-phone", body="Hello")


def test_send_sms_rejects_empty_phone_number() -> None:
    """send_sms raises ValueError for empty phone number."""
    with pytest.raises(ValueError, match="phone"):
        send_sms(to="", body="Hello")


def test_send_sms_rejects_empty_body() -> None:
    """send_sms raises ValueError for empty message body."""
    with pytest.raises(ValueError, match="body"):
        send_sms(to="+15551234567", body="")


@patch("src.delivery.sms.Client")
def test_send_sms_accepts_e164_format(mock_client_cls: MagicMock) -> None:
    """send_sms accepts valid E.164-formatted phone numbers."""
    mock_message = MagicMock()
    mock_message.sid = "SMvalid"
    mock_client_cls.return_value.messages.create.return_value = mock_message

    result = send_sms(to="+442071234567", body="Hello UK!")
    assert result.success is True

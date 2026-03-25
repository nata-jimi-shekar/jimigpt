"""Tests for delivery models — TDD: tests written before implementation."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.delivery.models import DeliveryChannel, DeliveryRequest, DeliveryResult
from src.messaging.generator import GeneratedMessage
from src.messaging.models import MessageIntent
from src.personality.models import ToneSpectrum

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _tone() -> ToneSpectrum:
    return ToneSpectrum(
        warmth=0.7,
        humor=0.4,
        directness=0.5,
        gravity=0.2,
        energy=0.6,
        vulnerability=0.3,
    )


def _generated_message() -> GeneratedMessage:
    return GeneratedMessage(
        message_id="msg-001",
        entity_id="entity-abc",
        content="Hey! Just thinking of you 🐾",
        generated_at=datetime.now(tz=UTC),
        model_used="claude-sonnet-4-6",
        prompt_tokens=50,
        completion_tokens=20,
        message_category="greeting",
        intended_intent=MessageIntent.AFFIRM,
        intended_tone=_tone(),
        character_count=28,
    )


# ---------------------------------------------------------------------------
# DeliveryChannel enum
# ---------------------------------------------------------------------------


def test_delivery_channel_sms_value() -> None:
    assert DeliveryChannel.SMS == "sms"


def test_delivery_channel_all_values() -> None:
    values = {c.value for c in DeliveryChannel}
    assert {"sms", "whatsapp", "voice", "push_notification"}.issubset(values)


# ---------------------------------------------------------------------------
# DeliveryRequest model
# ---------------------------------------------------------------------------


def test_delivery_request_valid() -> None:
    req = DeliveryRequest(
        message=_generated_message(),
        channel=DeliveryChannel.SMS,
        recipient_phone="+15551234567",
        scheduled_at=datetime.now(tz=UTC),
        timezone="America/New_York",
        recipient_id="user-xyz",
    )
    assert req.channel == DeliveryChannel.SMS
    assert req.recipient_phone == "+15551234567"
    assert req.recipient_id == "user-xyz"


def test_delivery_request_optional_fields_default() -> None:
    """recipient_phone and recipient_device_token are optional."""
    req = DeliveryRequest(
        message=_generated_message(),
        channel=DeliveryChannel.SMS,
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id="user-xyz",
    )
    assert req.recipient_phone is None
    assert req.recipient_device_token is None


def test_delivery_request_recipient_id_required() -> None:
    """recipient_id is required (foundation field for multi-recipient)."""
    with pytest.raises(ValidationError):
        DeliveryRequest(  # type: ignore[call-arg]
            message=_generated_message(),
            channel=DeliveryChannel.SMS,
            scheduled_at=datetime.now(tz=UTC),
            timezone="UTC",
            # recipient_id deliberately omitted
        )


def test_delivery_request_carries_generated_message() -> None:
    msg = _generated_message()
    req = DeliveryRequest(
        message=msg,
        channel=DeliveryChannel.SMS,
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id="user-xyz",
    )
    assert req.message.message_id == msg.message_id
    assert req.message.entity_id == msg.entity_id


# ---------------------------------------------------------------------------
# DeliveryResult model
# ---------------------------------------------------------------------------


def test_delivery_result_success() -> None:
    result = DeliveryResult(
        success=True,
        channel=DeliveryChannel.SMS,
        delivered_at=datetime.now(tz=UTC),
        external_id="SM1234567890abcdef",
        error=None,
    )
    assert result.success is True
    assert result.external_id == "SM1234567890abcdef"
    assert result.error is None


def test_delivery_result_failure() -> None:
    result = DeliveryResult(
        success=False,
        channel=DeliveryChannel.SMS,
        delivered_at=None,
        external_id=None,
        error="Twilio error: invalid phone number",
    )
    assert result.success is False
    assert result.delivered_at is None
    assert result.error == "Twilio error: invalid phone number"


def test_delivery_result_optional_fields() -> None:
    """delivered_at and external_id default to None."""
    result = DeliveryResult(
        success=True,
        channel=DeliveryChannel.SMS,
    )
    assert result.delivered_at is None
    assert result.external_id is None
    assert result.error is None


# ---------------------------------------------------------------------------
# Foundation field: recipient_id
# ---------------------------------------------------------------------------


def test_delivery_request_recipient_id_explicit() -> None:
    """Foundation field: recipient_id is explicit (not derived from entity owner)."""
    owner_id = "owner-111"
    req = DeliveryRequest(
        message=_generated_message(),
        channel=DeliveryChannel.SMS,
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id=owner_id,
    )
    assert req.recipient_id == owner_id


def test_delivery_request_recipient_id_different_from_entity() -> None:
    """Foundation: recipient_id is a separate field, not entity_id."""
    msg = _generated_message()  # entity_id = "entity-abc"
    req = DeliveryRequest(
        message=msg,
        channel=DeliveryChannel.SMS,
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id="different-user-999",
    )
    assert req.recipient_id != req.message.entity_id

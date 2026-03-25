"""Delivery layer models — channel, request, and result."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from src.messaging.generator import GeneratedMessage


class DeliveryChannel(StrEnum):
    """Supported delivery channels."""

    SMS = "sms"
    WHATSAPP = "whatsapp"
    VOICE = "voice"
    PUSH = "push_notification"


class DeliveryRequest(BaseModel):
    """A queued message ready for delivery."""

    message: GeneratedMessage
    channel: DeliveryChannel
    recipient_phone: str | None = None
    recipient_device_token: str | None = None
    scheduled_at: datetime
    timezone: str

    # Foundation field (F03 / multi-recipient): delivery targets a specific
    # person, not just "the entity owner". In Phase 1, this is always the
    # owner's user_id. In Phase 2 it can differ.
    recipient_id: str


class DeliveryResult(BaseModel):
    """Outcome of one delivery attempt."""

    success: bool
    channel: DeliveryChannel
    delivered_at: datetime | None = None
    external_id: str | None = None  # Twilio SID, push notification ID, etc.
    error: str | None = None

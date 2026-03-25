"""Delivery layer integration tests.

Exercises the full delivery flow end-to-end for both SMS and WhatsApp:

  GeneratedMessage
    → schedule_delivery()  [scheduler]
    → DeliveryQueue
    → get_pending_deliveries()
    → deliver_with_retry()  [sms — Twilio mocked]
    → DeliveryResult
    → POST /api/v1/webhooks/twilio  [webhook — sig bypassed]
    → get_delivery_status() / get_delivery_channel()

No real Twilio calls are made. The Twilio client is patched at the
src.delivery.sms.Client level. The webhook signature dependency is
overridden via FastAPI dependency_overrides.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.webhooks import (
    get_delivery_channel,
    get_delivery_status,
    reset_status_store,
    verify_twilio_signature,
)
from src.delivery.models import DeliveryChannel, DeliveryRequest, DeliveryResult
from src.delivery.scheduler import DeliveryQueue, get_pending_deliveries, schedule_delivery
from src.delivery.sms import MAX_ATTEMPTS, deliver_with_retry
from src.main import app
from src.messaging.generator import GeneratedMessage
from src.messaging.models import MessageIntent
from src.personality.models import ToneSpectrum

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_stores() -> None:
    """Reset webhook status store between tests."""
    reset_status_store()


@pytest.fixture()
def webhook_client() -> TestClient:
    """TestClient with signature verification bypassed."""
    app.dependency_overrides[verify_twilio_signature] = lambda: None
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def queue() -> DeliveryQueue:
    return DeliveryQueue()


def _tone() -> ToneSpectrum:
    return ToneSpectrum(
        warmth=0.7, humor=0.4, directness=0.5,
        gravity=0.2, energy=0.6, vulnerability=0.3,
    )


def _make_message(entity_id: str = "entity-jimi") -> GeneratedMessage:
    return GeneratedMessage(
        message_id=f"msg-{entity_id}",
        entity_id=entity_id,
        content="Hey! Thinking of you today 🐾",
        generated_at=datetime.now(tz=UTC),
        model_used="claude-sonnet-4-6",
        prompt_tokens=50,
        completion_tokens=20,
        message_category="greeting",
        intended_intent=MessageIntent.AFFIRM,
        intended_tone=_tone(),
        character_count=30,
    )


def _mock_twilio_success(sid: str = "SM_integration_001") -> MagicMock:
    mock_message = MagicMock()
    mock_message.sid = sid
    return mock_message


_NO_SLEEP = lambda _: None  # noqa: E731


# ---------------------------------------------------------------------------
# SMS — full happy path
# ---------------------------------------------------------------------------


def test_sms_full_flow_message_to_confirmed_delivery(
    queue: DeliveryQueue, webhook_client: TestClient
) -> None:
    """GeneratedMessage → schedule → queue → deliver (SMS) → webhook confirms."""
    msg = _make_message()

    # Step 1: schedule
    req = schedule_delivery(
        message=msg,
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        recipient_phone="+15551234567",
        queue=queue,
    )
    assert isinstance(req, DeliveryRequest)
    assert req.channel == DeliveryChannel.SMS

    # Step 2: retrieve pending
    current_time = datetime(2026, 3, 25, 11, 0, 0, tzinfo=UTC)
    pending = get_pending_deliveries(current_time, queue=queue)
    assert len(pending) == 1
    assert pending[0].message.message_id == msg.message_id

    # Step 3: deliver with mocked Twilio
    with patch("src.delivery.sms.Client") as mock_cls:
        mock_cls.return_value.messages.create.return_value = _mock_twilio_success("SM_sms_001")
        result = deliver_with_retry(req, _sleep_fn=_NO_SLEEP)

    assert result.success is True
    assert result.channel == DeliveryChannel.SMS
    assert result.external_id == "SM_sms_001"
    assert result.attempts == 1

    # Step 4: webhook confirms delivery
    response = webhook_client.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": result.external_id,
            "MessageStatus": "delivered",
            "From": "+15550001111",
        },
    )
    assert response.status_code == 200

    # Step 5: verify status store
    assert get_delivery_status(result.external_id) == "delivered"
    assert get_delivery_channel(result.external_id) == "sms"


# ---------------------------------------------------------------------------
# WhatsApp — full happy path
# ---------------------------------------------------------------------------


def test_whatsapp_full_flow_message_to_confirmed_delivery(
    queue: DeliveryQueue, webhook_client: TestClient
) -> None:
    """GeneratedMessage → schedule → queue → deliver (WhatsApp) → webhook confirms."""
    msg = _make_message(entity_id="entity-wa")

    # Step 1: schedule
    req = schedule_delivery(
        message=msg,
        channel=DeliveryChannel.WHATSAPP,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-co-001",
        recipient_phone="+573001234567",
        queue=queue,
    )
    assert req.channel == DeliveryChannel.WHATSAPP

    # Step 2: retrieve pending
    current_time = datetime(2026, 3, 25, 11, 0, 0, tzinfo=UTC)
    pending = get_pending_deliveries(current_time, queue=queue)
    assert len(pending) == 1

    # Step 3: deliver with mocked Twilio
    with patch("src.delivery.sms.Client") as mock_cls:
        mock_cls.return_value.messages.create.return_value = _mock_twilio_success("WA_wa_001")
        result = deliver_with_retry(req, _sleep_fn=_NO_SLEEP)

    assert result.success is True
    assert result.channel == DeliveryChannel.WHATSAPP
    assert result.external_id == "WA_wa_001"

    # Step 4: webhook confirms (WhatsApp From has "whatsapp:" prefix)
    response = webhook_client.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": result.external_id,
            "MessageStatus": "delivered",
            "From": "whatsapp:+14155238886",
        },
    )
    assert response.status_code == 200

    # Step 5: verify status and channel
    assert get_delivery_status(result.external_id) == "delivered"
    assert get_delivery_channel(result.external_id) == "whatsapp"


# ---------------------------------------------------------------------------
# Channel routing: deliver_with_retry uses the correct sender
# ---------------------------------------------------------------------------


def test_sms_request_calls_sms_sender(queue: DeliveryQueue) -> None:
    """deliver_with_retry routes SMS channel to send_sms, not send_whatsapp."""
    req = schedule_delivery(
        message=_make_message(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        recipient_phone="+15551234567",
        queue=queue,
    )

    with patch("src.delivery.sms.Client") as mock_cls:
        mock_cls.return_value.messages.create.return_value = _mock_twilio_success()
        deliver_with_retry(req, _sleep_fn=_NO_SLEEP)
        call_kwargs = mock_cls.return_value.messages.create.call_args.kwargs

    # SMS: to is plain E.164, no whatsapp: prefix
    assert not call_kwargs["to"].startswith("whatsapp:")
    assert not call_kwargs["from_"].startswith("whatsapp:")


def test_whatsapp_request_calls_whatsapp_sender(queue: DeliveryQueue) -> None:
    """deliver_with_retry routes WhatsApp channel to send_whatsapp, not send_sms."""
    req = schedule_delivery(
        message=_make_message(),
        channel=DeliveryChannel.WHATSAPP,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-co-001",
        recipient_phone="+573001234567",
        queue=queue,
    )

    with patch("src.delivery.sms.Client") as mock_cls:
        mock_cls.return_value.messages.create.return_value = _mock_twilio_success()
        deliver_with_retry(req, _sleep_fn=_NO_SLEEP)
        call_kwargs = mock_cls.return_value.messages.create.call_args.kwargs

    # WhatsApp: both to and from_ carry "whatsapp:" prefix
    assert call_kwargs["to"] == "whatsapp:+573001234567"
    assert call_kwargs["from_"].startswith("whatsapp:")


# ---------------------------------------------------------------------------
# Retry path — fail once, succeed on second attempt
# ---------------------------------------------------------------------------


def test_sms_retry_succeeds_on_second_attempt(queue: DeliveryQueue) -> None:
    """First Twilio call fails, second succeeds — retry loop works end-to-end."""
    req = schedule_delivery(
        message=_make_message(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        recipient_phone="+15551234567",
        queue=queue,
    )

    call_count = 0

    def send_fn(to: str, body: str) -> DeliveryResult:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return DeliveryResult(success=False, channel=DeliveryChannel.SMS, error="timeout")
        return DeliveryResult(
            success=True, channel=DeliveryChannel.SMS,
            delivered_at=datetime.now(tz=UTC), external_id="SM_retry_ok",
        )

    result = deliver_with_retry(req, _send_fn=send_fn, _sleep_fn=_NO_SLEEP)

    assert result.success is True
    assert result.attempts == 2
    assert call_count == 2


def test_whatsapp_retry_succeeds_on_second_attempt(queue: DeliveryQueue) -> None:
    """WhatsApp retry loop works end-to-end."""
    req = schedule_delivery(
        message=_make_message(),
        channel=DeliveryChannel.WHATSAPP,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-co-001",
        recipient_phone="+573001234567",
        queue=queue,
    )

    call_count = 0

    def send_fn(to: str, body: str) -> DeliveryResult:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return DeliveryResult(
                success=False, channel=DeliveryChannel.WHATSAPP, error="not opted in"
            )
        return DeliveryResult(
            success=True, channel=DeliveryChannel.WHATSAPP,
            delivered_at=datetime.now(tz=UTC), external_id="WA_retry_ok",
        )

    result = deliver_with_retry(req, _send_fn=send_fn, _sleep_fn=_NO_SLEEP)

    assert result.success is True
    assert result.attempts == 2


# ---------------------------------------------------------------------------
# Permanent failure — all 3 attempts fail
# ---------------------------------------------------------------------------


def test_all_attempts_fail_marks_permanently_failed(
    queue: DeliveryQueue, webhook_client: TestClient
) -> None:
    """All 3 attempts fail → result.success=False → webhook reports 'failed'."""
    req = schedule_delivery(
        message=_make_message(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        recipient_phone="+15551234567",
        queue=queue,
    )

    result = deliver_with_retry(
        req,
        _send_fn=lambda to, body: DeliveryResult(
            success=False, channel=DeliveryChannel.SMS, error="network down"
        ),
        _sleep_fn=_NO_SLEEP,
    )

    assert result.success is False
    assert result.attempts == MAX_ATTEMPTS

    # Simulate Twilio reporting 'failed' via webhook
    sid = "SM_perm_fail"
    webhook_client.post(
        "/api/v1/webhooks/twilio",
        data={"MessageSid": sid, "MessageStatus": "failed", "From": "+15550001111"},
    )
    assert get_delivery_status(sid) == "failed"


# ---------------------------------------------------------------------------
# Quiet hours — deferral flows through to scheduler correctly
# ---------------------------------------------------------------------------


def test_quiet_hours_message_not_pending_before_deferral(
    queue: DeliveryQueue,
) -> None:
    """Message scheduled at 23:00 is deferred to 07:00 next day — not yet pending at 23:30."""
    schedule_delivery(
        message=_make_message(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 23, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        recipient_phone="+15551234567",
        queue=queue,
    )

    # 23:30 same night — message is deferred, should NOT be pending
    before_deferral = datetime(2026, 3, 25, 23, 30, 0, tzinfo=UTC)
    assert get_pending_deliveries(before_deferral, queue=queue) == []


def test_quiet_hours_message_pending_after_deferral(queue: DeliveryQueue) -> None:
    """After quiet window ends the deferred message becomes pending and deliverable."""
    schedule_delivery(
        message=_make_message(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 23, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        recipient_phone="+15551234567",
        queue=queue,
    )

    # 07:01 next day — message should now be pending
    after_deferral = datetime(2026, 3, 26, 7, 1, 0, tzinfo=UTC)
    pending = get_pending_deliveries(after_deferral, queue=queue)
    assert len(pending) == 1


# ---------------------------------------------------------------------------
# Multi-channel: SMS and WhatsApp queued together
# ---------------------------------------------------------------------------


def test_sms_and_whatsapp_queued_and_delivered_independently(
    queue: DeliveryQueue, webhook_client: TestClient
) -> None:
    """SMS and WhatsApp requests can coexist in the queue and deliver independently."""
    msg_sms = _make_message(entity_id="entity-sms")
    msg_wa = _make_message(entity_id="entity-wa")

    schedule_delivery(
        message=msg_sms, channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0), timezone="UTC",
        recipient_id="user-sms", recipient_phone="+15551234567", queue=queue,
    )
    schedule_delivery(
        message=msg_wa, channel=DeliveryChannel.WHATSAPP,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0), timezone="UTC",
        recipient_id="user-wa", recipient_phone="+573001234567", queue=queue,
    )

    current_time = datetime(2026, 3, 25, 11, 0, 0, tzinfo=UTC)
    pending = get_pending_deliveries(current_time, queue=queue)
    assert len(pending) == 2

    channels = {r.channel for r in pending}
    assert DeliveryChannel.SMS in channels
    assert DeliveryChannel.WHATSAPP in channels

    # Deliver both
    with patch("src.delivery.sms.Client") as mock_cls:
        mock_cls.return_value.messages.create.side_effect = [
            _mock_twilio_success("SM_multi_001"),
            _mock_twilio_success("WA_multi_001"),
        ]
        results = [deliver_with_retry(r, _sleep_fn=_NO_SLEEP) for r in pending]

    assert all(r.success for r in results)
    sids = {r.external_id for r in results}
    assert "SM_multi_001" in sids
    assert "WA_multi_001" in sids

    # Webhook confirms both
    for r in results:
        from_field = (
            "whatsapp:+14155238886" if r.channel == DeliveryChannel.WHATSAPP
            else "+15550001111"
        )
        webhook_client.post(
            "/api/v1/webhooks/twilio",
            data={"MessageSid": r.external_id, "MessageStatus": "delivered", "From": from_field},
        )

    assert get_delivery_status("SM_multi_001") == "delivered"
    assert get_delivery_channel("SM_multi_001") == "sms"
    assert get_delivery_status("WA_multi_001") == "delivered"
    assert get_delivery_channel("WA_multi_001") == "whatsapp"

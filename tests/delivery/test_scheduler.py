"""Tests for delivery scheduler — TDD: tests written before implementation."""

from datetime import UTC, datetime, time

import pytest

from src.delivery.models import DeliveryChannel, DeliveryRequest
from src.delivery.scheduler import (
    DeliveryQueue,
    QuietHours,
    get_pending_deliveries,
    schedule_delivery,
)
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


def _msg(entity_id: str = "entity-abc") -> GeneratedMessage:
    return GeneratedMessage(
        message_id="msg-001",
        entity_id=entity_id,
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


@pytest.fixture()
def queue() -> DeliveryQueue:
    return DeliveryQueue()


# ---------------------------------------------------------------------------
# QuietHours model
# ---------------------------------------------------------------------------


def test_quiet_hours_defaults() -> None:
    qh = QuietHours()
    assert qh.start == time(22, 0)
    assert qh.end == time(7, 0)


def test_quiet_hours_custom() -> None:
    qh = QuietHours(start=time(23, 0), end=time(6, 0))
    assert qh.start == time(23, 0)
    assert qh.end == time(6, 0)


def test_quiet_hours_is_quiet_during_night() -> None:
    qh = QuietHours()
    assert qh.is_quiet(time(22, 30)) is True
    assert qh.is_quiet(time(0, 0)) is True
    assert qh.is_quiet(time(6, 59)) is True


def test_quiet_hours_not_quiet_during_day() -> None:
    qh = QuietHours()
    assert qh.is_quiet(time(7, 0)) is False
    assert qh.is_quiet(time(12, 0)) is False
    assert qh.is_quiet(time(21, 59)) is False


# ---------------------------------------------------------------------------
# schedule_delivery — timezone conversion
# ---------------------------------------------------------------------------


def test_schedule_delivery_converts_to_utc(queue: DeliveryQueue) -> None:
    """08:00 America/New_York is 13:00 UTC (EST, UTC-5)."""
    local_time = datetime(2026, 3, 25, 8, 0, 0)  # naive local time

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=local_time,
        timezone="America/New_York",
        recipient_id="user-001",
        recipient_phone="+15551234567",
        queue=queue,
    )

    # America/New_York in March is EDT (UTC-4), so 08:00 EDT = 12:00 UTC
    assert req.scheduled_at.tzinfo is not None  # always UTC-aware
    assert req.scheduled_at == req.scheduled_at.replace(tzinfo=UTC)
    # The UTC offset for America/New_York on 2026-03-25 is -4 (DST active)
    assert req.scheduled_at.hour == 12
    assert req.scheduled_at.minute == 0


def test_schedule_delivery_utc_timezone_unchanged(queue: DeliveryQueue) -> None:
    """Scheduling in UTC leaves the time unchanged."""
    local_time = datetime(2026, 3, 25, 15, 30, 0)

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=local_time,
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    assert req.scheduled_at.hour == 15
    assert req.scheduled_at.minute == 30


def test_schedule_delivery_returns_delivery_request(queue: DeliveryQueue) -> None:
    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )
    assert isinstance(req, DeliveryRequest)
    assert req.channel == DeliveryChannel.SMS
    assert req.recipient_id == "user-001"


# ---------------------------------------------------------------------------
# schedule_delivery — quiet hours enforcement
# ---------------------------------------------------------------------------


def test_schedule_during_quiet_hours_deferred_to_morning(queue: DeliveryQueue) -> None:
    """23:00 local is in quiet hours — deferred to 07:00 the same or next day."""
    local_time = datetime(2026, 3, 25, 23, 0, 0)  # 23:00 UTC (quiet)

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=local_time,
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    # Should be deferred to 07:00 next day
    assert req.scheduled_at.hour == 7
    assert req.scheduled_at.day == 26  # next day


def test_schedule_at_midnight_deferred_to_morning(queue: DeliveryQueue) -> None:
    """00:00 UTC is in quiet hours — deferred to 07:00."""
    local_time = datetime(2026, 3, 25, 0, 0, 0)

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=local_time,
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    assert req.scheduled_at.hour == 7


def test_schedule_just_before_quiet_start_not_deferred(queue: DeliveryQueue) -> None:
    """21:59 is NOT in quiet hours — scheduled as-is."""
    local_time = datetime(2026, 3, 25, 21, 59, 0)

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=local_time,
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    assert req.scheduled_at.hour == 21
    assert req.scheduled_at.minute == 59


def test_schedule_at_quiet_end_not_deferred(queue: DeliveryQueue) -> None:
    """07:00 exactly is the first valid time — not deferred."""
    local_time = datetime(2026, 3, 25, 7, 0, 0)

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=local_time,
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    assert req.scheduled_at.hour == 7


def test_schedule_quiet_hours_custom(queue: DeliveryQueue) -> None:
    """Custom quiet hours (23:00-06:00) are respected."""
    local_time = datetime(2026, 3, 25, 23, 30, 0)
    qh = QuietHours(start=time(23, 0), end=time(6, 0))

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=local_time,
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
        quiet_hours=qh,
    )

    assert req.scheduled_at.hour == 6
    assert req.scheduled_at.day == 26


def test_schedule_timezone_quiet_hours_checked_in_local_time(
    queue: DeliveryQueue,
) -> None:
    """Quiet hours enforced in the user's local timezone, not UTC."""
    # 23:00 America/New_York = 03:00 UTC next day (quiet in local)
    # Without local enforcement, 03:00 UTC might mistakenly pass UTC check
    local_time = datetime(2026, 3, 25, 23, 0, 0)  # 23:00 local = quiet hours

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=local_time,
        timezone="America/New_York",
        recipient_id="user-001",
        queue=queue,
    )

    # Must be deferred — 23:00 local is in quiet hours
    # 07:00 local America/New_York (EDT) = 11:00 UTC
    assert req.scheduled_at.hour == 11  # 07:00 EDT = 11:00 UTC


# ---------------------------------------------------------------------------
# get_pending_deliveries
# ---------------------------------------------------------------------------


def test_get_pending_returns_due_deliveries(queue: DeliveryQueue) -> None:
    """Deliveries with scheduled_at <= current_time are returned."""
    past_time = datetime(2026, 3, 25, 8, 0, 0)
    schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=past_time,
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    current_time = datetime(2026, 3, 25, 9, 0, 0, tzinfo=UTC)
    pending = get_pending_deliveries(current_time, queue=queue)

    assert len(pending) == 1


def test_get_pending_excludes_future_deliveries(queue: DeliveryQueue) -> None:
    """Deliveries with scheduled_at > current_time are NOT returned."""
    future_time = datetime(2026, 3, 25, 20, 0, 0)
    schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=future_time,
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    current_time = datetime(2026, 3, 25, 9, 0, 0, tzinfo=UTC)
    pending = get_pending_deliveries(current_time, queue=queue)

    assert len(pending) == 0


def test_get_pending_returns_multiple(queue: DeliveryQueue) -> None:
    """Multiple due deliveries are all returned."""
    for i in range(3):
        schedule_delivery(
            message=_msg(entity_id=f"entity-{i}"),
            channel=DeliveryChannel.SMS,
            scheduled_time=datetime(2026, 3, 25, 8, i, 0),
            timezone="UTC",
            recipient_id=f"user-{i}",
            queue=queue,
        )

    current_time = datetime(2026, 3, 25, 10, 0, 0, tzinfo=UTC)
    pending = get_pending_deliveries(current_time, queue=queue)

    assert len(pending) == 3


def test_get_pending_empty_queue(queue: DeliveryQueue) -> None:
    current_time = datetime(2026, 3, 25, 10, 0, 0, tzinfo=UTC)
    assert get_pending_deliveries(current_time, queue=queue) == []


# ---------------------------------------------------------------------------
# Multi-recipient: no unique constraint on entity_id + recipient_id
# ---------------------------------------------------------------------------


def test_same_entity_multiple_recipients_allowed(queue: DeliveryQueue) -> None:
    """Same entity can be scheduled for different recipients (Phase 2 foundation)."""
    msg = _msg(entity_id="entity-abc")

    for i in range(3):
        schedule_delivery(
            message=msg,
            channel=DeliveryChannel.SMS,
            scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
            timezone="UTC",
            recipient_id=f"user-{i}",
            queue=queue,
        )

    current_time = datetime(2026, 3, 25, 11, 0, 0, tzinfo=UTC)
    pending = get_pending_deliveries(current_time, queue=queue)
    assert len(pending) == 3
    recipient_ids = {r.recipient_id for r in pending}
    assert recipient_ids == {"user-0", "user-1", "user-2"}


# ---------------------------------------------------------------------------
# Foundation field: active_arcs
# ---------------------------------------------------------------------------


def test_dst_spring_forward_nonexistent_time_normalised(queue: DeliveryQueue) -> None:
    """2026-03-08 02:30 America/New_York doesn't exist (spring forward).

    Using custom quiet hours (23:00-01:00) so 02:30 is NOT deferred.
    replace(tzinfo=tz) silently gives wrong UTC; DST-safe localization
    should normalise to the post-transition wall-clock equivalent
    (03:30 EDT = 07:30 UTC).
    """
    no_conflict_qh = QuietHours(start=time(23, 0), end=time(1, 0))
    nonexistent = datetime(2026, 3, 8, 2, 30, 0)

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=nonexistent,
        timezone="America/New_York",
        recipient_id="user-001",
        queue=queue,
        quiet_hours=no_conflict_qh,
    )

    # After normalisation the UTC time should be 07:30
    # (03:30 EDT = 07:30 UTC — the fold-forward equivalent)
    assert req.scheduled_at.hour == 7
    assert req.scheduled_at.minute == 30


def test_dst_fall_back_ambiguous_time_uses_first_occurrence(
    queue: DeliveryQueue,
) -> None:
    """2026-11-01 01:30 America/New_York is ambiguous (fall back).

    Using custom quiet hours (23:00-01:00) so 01:30 is NOT deferred.
    Should use the first (DST/EDT) occurrence: 01:30 EDT = 05:30 UTC.
    """
    no_conflict_qh = QuietHours(start=time(23, 0), end=time(1, 0))
    ambiguous = datetime(2026, 11, 1, 1, 30, 0)

    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=ambiguous,
        timezone="America/New_York",
        recipient_id="user-001",
        queue=queue,
        quiet_hours=no_conflict_qh,
    )

    # First occurrence (EDT, UTC-4): 01:30 EDT = 05:30 UTC
    assert req.scheduled_at.hour == 5
    assert req.scheduled_at.minute == 30


def test_schedule_delivery_accepts_active_arcs_none(queue: DeliveryQueue) -> None:
    """Foundation field: active_arcs defaults to None without changing behaviour."""
    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
        active_arcs=None,
    )
    assert req is not None


def test_pending_does_not_return_claimed_items(queue: DeliveryQueue) -> None:
    """Claiming items removes them from future pending() calls — no duplicates."""
    schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 8, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    current_time = datetime(2026, 3, 25, 9, 0, 0, tzinfo=UTC)

    # First call: returns the item
    first = queue.claim(current_time)
    assert len(first) == 1

    # Second call: item already claimed — must be empty
    second = queue.claim(current_time)
    assert len(second) == 0


def test_pending_still_shows_unclaimed_items(queue: DeliveryQueue) -> None:
    """pending() still shows items (read-only view), claim() removes them."""
    schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 8, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )

    current_time = datetime(2026, 3, 25, 9, 0, 0, tzinfo=UTC)

    # pending() is a read-only view — items remain
    assert len(queue.pending(current_time)) == 1
    assert len(queue.pending(current_time)) == 1

    # claim() removes them
    claimed = queue.claim(current_time)
    assert len(claimed) == 1
    assert len(queue.pending(current_time)) == 0


def test_claim_only_returns_due_items(queue: DeliveryQueue) -> None:
    """claim() only claims items with scheduled_at <= at, leaving future items."""
    schedule_delivery(
        message=_msg(entity_id="due"),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 8, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
    )
    schedule_delivery(
        message=_msg(entity_id="future"),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 20, 0, 0),
        timezone="UTC",
        recipient_id="user-002",
        queue=queue,
    )

    at_9am = datetime(2026, 3, 25, 9, 0, 0, tzinfo=UTC)
    claimed = queue.claim(at_9am)
    assert len(claimed) == 1
    assert claimed[0].message.entity_id == "due"

    # Future item still pending later
    at_9pm = datetime(2026, 3, 25, 21, 0, 0, tzinfo=UTC)
    claimed_later = queue.claim(at_9pm)
    assert len(claimed_later) == 1
    assert claimed_later[0].message.entity_id == "future"


def test_schedule_delivery_accepts_active_arcs_list(queue: DeliveryQueue) -> None:
    """Foundation field: active_arcs can receive arc dicts without error."""
    arc_data = [{"arc_id": "arc-001", "position": 1}]
    req = schedule_delivery(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        scheduled_time=datetime(2026, 3, 25, 10, 0, 0),
        timezone="UTC",
        recipient_id="user-001",
        queue=queue,
        active_arcs=arc_data,
    )
    assert req is not None

"""Delivery scheduler — timezone-aware scheduling with quiet hours enforcement.

schedule_delivery() converts a naive local datetime to UTC, enforces quiet
hours in the user's timezone, and enqueues a DeliveryRequest.

get_pending_deliveries() returns all queued requests whose scheduled_at
is at or before the given current_time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from src.delivery.models import DeliveryChannel, DeliveryRequest

if TYPE_CHECKING:
    from src.messaging.generator import GeneratedMessage

# Default quiet window: 22:00 – 07:00 local (no messages)
_DEFAULT_QUIET_START = time(22, 0)
_DEFAULT_QUIET_END = time(7, 0)


class QuietHours(BaseModel):
    """Configurable quiet window. Messages scheduled inside are deferred."""

    start: time = _DEFAULT_QUIET_START  # inclusive
    end: time = _DEFAULT_QUIET_END      # exclusive (first valid minute)

    def is_quiet(self, t: time) -> bool:
        """Return True if *t* falls inside the quiet window.

        Handles overnight ranges (start > end, e.g. 22:00–07:00).
        """
        if self.start > self.end:
            # Overnight: quiet from start until midnight, then midnight to end
            return t >= self.start or t < self.end
        # Same-day range (unusual but supported)
        return self.start <= t < self.end


@dataclass
class DeliveryQueue:
    """In-memory delivery queue for Phase 1.

    Phase 2+ will replace the backing store with Supabase delivery_queue table.
    No unique constraint on (entity_id, recipient_id) — the same entity can
    deliver to multiple recipients (multi-recipient foundation, F03).
    """

    _items: list[DeliveryRequest] = field(default_factory=list)

    def enqueue(self, request: DeliveryRequest) -> None:
        self._items.append(request)

    def pending(self, at: datetime) -> list[DeliveryRequest]:
        """Return all requests with scheduled_at <= at (read-only view)."""
        at_utc = at if at.tzinfo is not None else at.replace(tzinfo=UTC)
        return [r for r in self._items if r.scheduled_at <= at_utc]

    def claim(self, at: datetime) -> list[DeliveryRequest]:
        """Atomically return and remove all requests with scheduled_at <= at.

        Unlike pending(), this dequeues the items so they are never returned
        again — preventing duplicate delivery on repeated polling.
        """
        at_utc = at if at.tzinfo is not None else at.replace(tzinfo=UTC)
        due = [r for r in self._items if r.scheduled_at <= at_utc]
        self._items = [r for r in self._items if r.scheduled_at > at_utc]
        return due


def _to_utc(local_naive: datetime, tz: ZoneInfo) -> datetime:
    """Localise a naive datetime in *tz* and convert to UTC.

    Uses ``tz.fromutc()`` round-trip to handle DST correctly:
    - Nonexistent times (spring forward): normalised to the post-transition
      wall-clock equivalent (e.g., 02:30 → 03:30 EDT).
    - Ambiguous times (fall back): resolved to the *first* occurrence
      (the DST/summer side, fold=0).
    """
    # Estimate UTC by assuming the standard offset, then let fromutc()
    # pick the correct wall-clock time. This avoids replace(tzinfo=tz)
    # which silently accepts nonexistent/ambiguous local times.
    # fold=0 → prefer the first (DST) occurrence for ambiguous times.
    aware = local_naive.replace(tzinfo=tz, fold=0)
    utc_guess = aware.astimezone(UTC)
    # Round-trip through fromutc to normalise nonexistent times
    normalised = utc_guess.astimezone(tz)
    return normalised.astimezone(UTC)


def _defer_to_quiet_end(local_naive: datetime, quiet: QuietHours) -> datetime:
    """Advance *local_naive* to the first moment after the quiet window."""
    next_day = local_naive.date() + timedelta(days=1)
    return datetime.combine(next_day, quiet.end)


def schedule_delivery(
    message: GeneratedMessage,
    channel: DeliveryChannel,
    scheduled_time: datetime,
    timezone: str,
    recipient_id: str,
    recipient_phone: str | None = None,
    recipient_device_token: str | None = None,
    quiet_hours: QuietHours | None = None,
    queue: DeliveryQueue | None = None,
    # Foundation field (Phase 2 — arc-aware scheduling): arc timing may
    # override or adjust the default schedule window.
    active_arcs: list[dict[str, object]] | None = None,
) -> DeliveryRequest:
    """Schedule a message for delivery at *scheduled_time* in *timezone*.

    1. Interprets *scheduled_time* as a naive local datetime in *timezone*.
    2. Enforces quiet hours (checked in local time, not UTC).
    3. Converts the (possibly deferred) time to UTC.
    4. Enqueues and returns a DeliveryRequest.

    ``active_arcs`` is a Phase 2 foundation field — accepted but unused in
    Phase 1; defaults to None and does not change behaviour.
    """
    qh = quiet_hours or QuietHours()
    tz = ZoneInfo(timezone)

    # Strip tzinfo so we always treat scheduled_time as a naive local value
    local_naive = scheduled_time.replace(tzinfo=None)

    if qh.is_quiet(local_naive.time()):
        local_naive = _defer_to_quiet_end(local_naive, qh)

    scheduled_utc = _to_utc(local_naive, tz)

    request = DeliveryRequest(
        message=message,
        channel=channel,
        recipient_phone=recipient_phone,
        recipient_device_token=recipient_device_token,
        scheduled_at=scheduled_utc,
        timezone=timezone,
        recipient_id=recipient_id,
    )

    if queue is not None:
        queue.enqueue(request)

    return request


def get_pending_deliveries(
    current_time: datetime,
    queue: DeliveryQueue | None = None,
) -> list[DeliveryRequest]:
    """Return all queued DeliveryRequests whose scheduled_at <= current_time."""
    if queue is None:
        return []
    return queue.pending(current_time)

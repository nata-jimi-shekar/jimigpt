"""Context signal models, TIME collector, and SignalCollector framework."""

import logging
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Type for a synchronous signal collector function.
CollectorFn = Callable[[str, str, datetime], list["ContextSignal"]]

_DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class ContextSignalSource(StrEnum):
    """Where context signals come from.

    Phase 1 collectors: TIME, INTERACTION, SEASONAL.
    Phase 2: WEATHER, CALENDAR.
    Phase 3: LOCATION, DEVICE.
    Foundation: USER_CONTEXT (enum value only — no collector in Phase 1).
    """

    TIME = "time"
    WEATHER = "weather"
    CALENDAR = "calendar"
    LOCATION = "location"
    INTERACTION = "interaction"
    SEASONAL = "seasonal"
    ENTITY_MEMORY = "entity_memory"
    DEVICE = "device"

    # --- Phase 2 Foundation ---
    # Enum value defined now; collector implemented in Phase 2 once reply
    # classification extracts context_tags from user replies.
    USER_CONTEXT = "user_context"


class ContextSignal(BaseModel):
    """A single contextual signal that influences message composition."""

    source: ContextSignalSource
    signal_key: str
    signal_value: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime


class ContextSignalBundle(BaseModel):
    """All active signals for a message generation moment."""

    signals: list[ContextSignal]
    user_id: str
    entity_id: str
    generated_at: datetime

    def get_signal(self, key: str) -> ContextSignal | None:
        """Return the first signal matching key, or None."""
        return next((s for s in self.signals if s.signal_key == key), None)

    def has_signal(self, source: ContextSignalSource) -> bool:
        """Return True if any signal from source is present."""
        return any(s.source == source for s in self.signals)


class SignalCollector:
    """Collects context signals from registered source collectors.

    Collectors are registered per source. Missing collectors produce no signals
    (graceful degradation). Collectors that raise are logged and skipped.
    """

    def __init__(self) -> None:
        self._collectors: dict[ContextSignalSource, CollectorFn] = {}

    def register_collector(self, source: ContextSignalSource, collector: CollectorFn) -> None:
        """Register a collector function for a signal source."""
        self._collectors[source] = collector

    async def collect(
        self,
        user_id: str,
        entity_id: str,
        current_time: datetime,
    ) -> ContextSignalBundle:
        """Collect all signals from registered sources.

        Each source runs independently. Failures are logged and skipped.
        """
        signals: list[ContextSignal] = []

        for source, collector_fn in self._collectors.items():
            try:
                signals.extend(collector_fn(user_id, entity_id, current_time))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Signal collector for %s failed: %s", source, exc)

        return ContextSignalBundle(
            signals=signals,
            user_id=user_id,
            entity_id=entity_id,
            generated_at=current_time,
        )


# ---------------------------------------------------------------------------
# TIME collector
# ---------------------------------------------------------------------------


def collect_time_signals(
    user_id: str,
    entity_id: str,
    current_time: datetime,
) -> list[ContextSignal]:
    """Produce TIME-source signals for time_of_day, day_of_week, and day_type.

    Boundaries:
      late_night   00:00–04:59
      early_morning 05:00–07:59
      morning      08:00–11:59
      midday       12:00–13:59
      afternoon    14:00–17:59
      evening      18:00–20:59
      night        21:00–23:59
    """
    hour = current_time.hour

    if hour < 5:
        time_of_day = "late_night"
    elif hour < 8:
        time_of_day = "early_morning"
    elif hour < 12:
        time_of_day = "morning"
    elif hour < 14:
        time_of_day = "midday"
    elif hour < 18:
        time_of_day = "afternoon"
    elif hour < 21:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    weekday = current_time.weekday()  # 0=Monday, 6=Sunday
    day_of_week = _DAY_NAMES[weekday]
    day_type = "weekend" if weekday >= 5 else "workday"

    return [
        ContextSignal(
            source=ContextSignalSource.TIME,
            signal_key="time_of_day",
            signal_value=time_of_day,
            timestamp=current_time,
        ),
        ContextSignal(
            source=ContextSignalSource.TIME,
            signal_key="day_of_week",
            signal_value=day_of_week,
            timestamp=current_time,
        ),
        ContextSignal(
            source=ContextSignalSource.TIME,
            signal_key="day_type",
            signal_value=day_type,
            timestamp=current_time,
        ),
    ]

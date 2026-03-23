"""SEASONAL signal collector — season and entity anniversary signals."""

from datetime import datetime

from pydantic import BaseModel

from src.messaging.signals import ContextSignal, ContextSignalSource

# Month → season (Northern Hemisphere)
_MONTH_TO_SEASON: dict[int, str] = {
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "fall",
    10: "fall",
    11: "fall",
    12: "winter",
}


class SeasonalData(BaseModel):
    """Input data for the SEASONAL signal collector."""

    entity_created_at: datetime


def collect_seasonal_signals(
    user_id: str,
    entity_id: str,
    current_time: datetime,
    seasonal_data: SeasonalData,
) -> list[ContextSignal]:
    """Produce SEASONAL-source signals: season and entity_anniversary.

    Anniversary is true when the month/day matches the entity creation date
    and at least one full year has elapsed.
    """
    season = _MONTH_TO_SEASON[current_time.month]

    created = seasonal_data.entity_created_at
    is_anniversary = (
        current_time.month == created.month
        and current_time.day == created.day
        and current_time.year > created.year
    )

    return [
        ContextSignal(
            source=ContextSignalSource.SEASONAL,
            signal_key="seasonal:season",
            signal_value=season,
            timestamp=current_time,
        ),
        ContextSignal(
            source=ContextSignalSource.SEASONAL,
            signal_key="seasonal:entity_anniversary",
            signal_value="true" if is_anniversary else "false",
            timestamp=current_time,
        ),
    ]

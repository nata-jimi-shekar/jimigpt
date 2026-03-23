"""Random interval trigger evaluation."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.messaging.triggers import TriggerRule, TriggerType

_DEFAULT_MAX_PER_DAY = 5
_MIN_GAP = timedelta(hours=2)


def evaluate_random_trigger(
    rule: TriggerRule,
    current_time: datetime,
    last_fired: datetime | None,
    messages_today: int = 0,
    max_per_day: int = _DEFAULT_MAX_PER_DAY,
) -> bool:
    """Return True if a RANDOM_INTERVAL trigger is eligible to fire now.

    Enforces (in order):
    1. Rule is enabled and type is RANDOM_INTERVAL.
    2. Daily message cap not exceeded (default: max 5/day).
    3. Minimum 2-hour gap since last_fired (skipped if last_fired is None).
    4. Current time falls within window_start/window_end in the rule's
       timezone (skipped if either bound is unset).

    The caller is responsible for any probabilistic firing decision — this
    function only checks whether firing is *permitted* right now.
    """
    if not rule.enabled:
        return False

    if rule.trigger_type != TriggerType.RANDOM_INTERVAL:
        return False

    if messages_today >= max_per_day:
        return False

    if last_fired is not None and (current_time - last_fired) < _MIN_GAP:
        return False

    if rule.window_start is not None and rule.window_end is not None:
        tz = ZoneInfo(rule.timezone)
        local_now = current_time.astimezone(tz)
        local_time = local_now.time().replace(second=0, microsecond=0)
        if not (_parse_hhmm(rule.window_start) <= local_time < _parse_hhmm(rule.window_end)):
            return False

    return True


def _parse_hhmm(hhmm: str) -> time:
    """Parse an "HH:MM" string into a time object."""
    h, m = map(int, hhmm.split(":"))
    return time(h, m)

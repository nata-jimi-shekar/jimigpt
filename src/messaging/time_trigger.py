"""Time-based trigger evaluation."""

import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from croniter import croniter

from src.messaging.triggers import TriggerRule, TriggerType

logger = logging.getLogger(__name__)


def evaluate_time_trigger(
    rule: TriggerRule,
    current_time: datetime,
    timezone: str,
) -> bool:
    """Return True if a TIME_BASED trigger fires at current_time in timezone.

    Checks (in order):
    1. Rule is enabled.
    2. Rule type is TIME_BASED with a schedule_cron.
    3. Cron fires at current_time (to the minute) expressed in timezone.
    4. If both window_start and window_end are set, the local time is within
       [window_start, window_end) — this is the quiet-hours guard.
    """
    if not rule.enabled:
        return False

    if rule.trigger_type != TriggerType.TIME_BASED:
        return False

    if not rule.schedule_cron:
        return False

    tz = ZoneInfo(timezone)
    local_now = current_time.astimezone(tz)
    local_minute = local_now.replace(second=0, microsecond=0, tzinfo=None)

    # croniter works with naive datetimes.
    # Base is 1 second before the target minute so get_next() lands on it.
    base = local_minute - timedelta(seconds=1)
    try:
        it = croniter(rule.schedule_cron, base)
        next_fire: datetime = it.get_next(datetime)
    except (ValueError, KeyError, TypeError) as exc:
        logger.warning("Invalid cron expression %r for rule %s: %s", rule.schedule_cron, rule.rule_id, exc)
        return False

    if next_fire != local_minute:
        return False

    # Quiet-hours check: both fields must be set for the window to apply.
    if rule.window_start is not None and rule.window_end is not None:
        local_time = local_now.time().replace(second=0, microsecond=0)
        if not (_parse_hhmm(rule.window_start) <= local_time < _parse_hhmm(rule.window_end)):
            return False

    return True


def _parse_hhmm(hhmm: str) -> time:
    """Parse an "HH:MM" string into a time object."""
    h, m = map(int, hhmm.split(":"))
    return time(h, m)

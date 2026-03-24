"""Tests for time-based trigger evaluation."""

from datetime import datetime, timezone

import pytest

from src.messaging.triggers import TriggerRule, TriggerType
from src.messaging.time_trigger import evaluate_time_trigger

UTC = timezone.utc


def _time_rule(**kwargs) -> TriggerRule:
    defaults = dict(
        rule_id="r1",
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="entity-001",
        message_category="greeting",
        schedule_cron="0 8 * * *",
    )
    defaults.update(kwargs)
    return TriggerRule(**defaults)


# ---------------------------------------------------------------------------
# Fires at the correct cron time
# ---------------------------------------------------------------------------


def test_fires_at_scheduled_cron_minute() -> None:
    rule = _time_rule(schedule_cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is True


def test_does_not_fire_one_minute_past_cron() -> None:
    rule = _time_rule(schedule_cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 1, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


def test_does_not_fire_one_hour_before_cron() -> None:
    rule = _time_rule(schedule_cron="0 8 * * *")
    now = datetime(2026, 3, 23, 7, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


def test_fires_at_non_hour_cron_time() -> None:
    # "30 14 * * *" = 14:30
    rule = _time_rule(schedule_cron="30 14 * * *")
    now = datetime(2026, 3, 23, 14, 30, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is True


def test_does_not_fire_at_wrong_minute_for_non_hour_cron() -> None:
    rule = _time_rule(schedule_cron="30 14 * * *")
    now = datetime(2026, 3, 23, 14, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


# ---------------------------------------------------------------------------
# Disabled rule never fires
# ---------------------------------------------------------------------------


def test_disabled_rule_does_not_fire() -> None:
    rule = _time_rule(enabled=False)
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


# ---------------------------------------------------------------------------
# Wrong trigger type does not fire
# ---------------------------------------------------------------------------


def test_random_interval_rule_does_not_fire() -> None:
    rule = _time_rule(trigger_type=TriggerType.RANDOM_INTERVAL)
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


def test_event_based_rule_does_not_fire() -> None:
    rule = _time_rule(trigger_type=TriggerType.EVENT_BASED)
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


# ---------------------------------------------------------------------------
# Missing cron does not fire
# ---------------------------------------------------------------------------


def test_missing_cron_does_not_fire() -> None:
    rule = _time_rule(schedule_cron=None)
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


# ---------------------------------------------------------------------------
# Quiet hours — window_start / window_end
# ---------------------------------------------------------------------------


def test_fires_within_quiet_hours_window() -> None:
    rule = _time_rule(
        schedule_cron="0 10 * * *",
        window_start="08:00",
        window_end="22:00",
    )
    now = datetime(2026, 3, 23, 10, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is True


def test_does_not_fire_before_window_start() -> None:
    # Cron at 07:00, window opens at 08:00
    rule = _time_rule(
        schedule_cron="0 7 * * *",
        window_start="08:00",
        window_end="22:00",
    )
    now = datetime(2026, 3, 23, 7, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


def test_does_not_fire_at_or_after_window_end() -> None:
    # Cron at 22:00, window ends at 22:00 (exclusive)
    rule = _time_rule(
        schedule_cron="0 22 * * *",
        window_start="08:00",
        window_end="22:00",
    )
    now = datetime(2026, 3, 23, 22, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


def test_fires_at_window_start_boundary() -> None:
    # Cron fires exactly at window_start — should be allowed (inclusive start)
    rule = _time_rule(
        schedule_cron="0 8 * * *",
        window_start="08:00",
        window_end="22:00",
    )
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is True


def test_no_window_does_not_restrict_firing() -> None:
    # Without window_start/window_end, any time is valid
    rule = _time_rule(schedule_cron="0 3 * * *")
    now = datetime(2026, 3, 23, 3, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is True


def test_only_window_start_set_does_not_restrict() -> None:
    # Both must be set for window to apply
    rule = _time_rule(schedule_cron="0 7 * * *", window_start="08:00")
    now = datetime(2026, 3, 23, 7, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is True


# ---------------------------------------------------------------------------
# Timezone conversion
# ---------------------------------------------------------------------------


def test_fires_at_correct_local_time_in_eastern_winter() -> None:
    # Cron "0 8 * * *" in America/New_York (EST = UTC-5 in January)
    # 8am NY = 13:00 UTC
    rule = _time_rule(schedule_cron="0 8 * * *")
    now = datetime(2026, 1, 23, 13, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "America/New_York") is True


def test_does_not_fire_at_utc_time_when_eastern_winter_timezone_set() -> None:
    # 8am UTC = 3am NY (EST) — should not fire for an 8am NY cron
    rule = _time_rule(schedule_cron="0 8 * * *")
    now = datetime(2026, 1, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "America/New_York") is False


def test_fires_at_correct_local_time_in_eastern_summer() -> None:
    # EDT = UTC-4 in summer. 8am NY (EDT) = 12:00 UTC
    # March 23, 2026 is in EDT (DST starts March 8, 2026)
    rule = _time_rule(schedule_cron="0 8 * * *")
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "America/New_York") is True


def test_timezone_and_window_interact_correctly() -> None:
    # Cron at 8am UTC, evaluated in NY (EDT, UTC-4) = 4am local
    # Window 08:00-22:00 NY time → 4am is outside window → should not fire
    rule = _time_rule(
        schedule_cron="0 8 * * *",
        window_start="08:00",
        window_end="22:00",
    )
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    # 8am UTC = 4am EDT — cron fires at 8am UTC, but locally it's 4am (outside window)
    assert evaluate_time_trigger(rule, now, "America/New_York") is False


# ---------------------------------------------------------------------------
# Codex review fix: invalid cron expressions must fail closed
# ---------------------------------------------------------------------------


def test_invalid_cron_expression_returns_false() -> None:
    """Malformed cron should return False, not raise."""
    rule = _time_rule(schedule_cron="INVALID CRON")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False


def test_partial_cron_expression_returns_false() -> None:
    """Incomplete cron (too few fields) should return False, not raise."""
    rule = _time_rule(schedule_cron="0 8 *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    assert evaluate_time_trigger(rule, now, "UTC") is False

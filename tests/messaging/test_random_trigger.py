"""Tests for random interval trigger evaluation."""

from datetime import datetime, timedelta, timezone

import pytest

from src.messaging.triggers import TriggerRule, TriggerType
from src.messaging.random_trigger import evaluate_random_trigger

UTC = timezone.utc


def _random_rule(**kwargs) -> TriggerRule:
    defaults = dict(
        rule_id="r1",
        trigger_type=TriggerType.RANDOM_INTERVAL,
        product="jimigpt",
        entity_id="entity-001",
        message_category="caring",
        window_start="09:00",
        window_end="21:00",
    )
    defaults.update(kwargs)
    return TriggerRule(**defaults)


# ---------------------------------------------------------------------------
# Window (quiet hours)
# ---------------------------------------------------------------------------


def test_fires_within_window() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)  # noon UTC, within 09-21
    assert evaluate_random_trigger(rule, now, last_fired=None) is True


def test_does_not_fire_before_window_start() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 8, 59, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is False


def test_does_not_fire_at_or_after_window_end() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 21, 0, tzinfo=UTC)  # 21:00 is exclusive end
    assert evaluate_random_trigger(rule, now, last_fired=None) is False


def test_fires_at_window_start_boundary() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 9, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is True


def test_fires_at_window_end_minus_one_minute() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 20, 59, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is True


def test_no_window_set_does_not_restrict_time() -> None:
    rule = _random_rule(window_start=None, window_end=None)
    now = datetime(2026, 3, 23, 3, 0, tzinfo=UTC)  # early morning, no window
    assert evaluate_random_trigger(rule, now, last_fired=None) is True


def test_only_window_start_set_does_not_restrict() -> None:
    # Both must be present for the window to apply
    rule = _random_rule(window_end=None)
    now = datetime(2026, 3, 23, 7, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is True


# ---------------------------------------------------------------------------
# Timezone: window is evaluated in the rule's timezone
# ---------------------------------------------------------------------------


def test_window_evaluated_in_rule_timezone() -> None:
    # Window 09:00-21:00 in America/New_York (EDT = UTC-4)
    # 09:00 EDT = 13:00 UTC → current_time 12:00 UTC = 08:00 EDT → outside window
    rule = _random_rule(timezone="America/New_York")
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)  # 08:00 EDT — before 09:00 window
    assert evaluate_random_trigger(rule, now, last_fired=None) is False


def test_window_evaluated_in_rule_timezone_inside() -> None:
    # 14:00 UTC = 10:00 EDT → inside 09:00-21:00 window
    rule = _random_rule(timezone="America/New_York")
    now = datetime(2026, 3, 23, 14, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is True


# ---------------------------------------------------------------------------
# Minimum 2-hour gap
# ---------------------------------------------------------------------------


def test_does_not_fire_within_2_hour_gap() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    last_fired = now - timedelta(hours=1, minutes=59)
    assert evaluate_random_trigger(rule, now, last_fired=last_fired) is False


def test_fires_after_exactly_2_hour_gap() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    last_fired = now - timedelta(hours=2)
    assert evaluate_random_trigger(rule, now, last_fired=last_fired) is True


def test_fires_after_more_than_2_hour_gap() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 14, 0, tzinfo=UTC)
    last_fired = now - timedelta(hours=3)
    assert evaluate_random_trigger(rule, now, last_fired=last_fired) is True


def test_no_last_fired_skips_gap_check() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is True


def test_gap_just_under_2_hours_blocked() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    last_fired = now - timedelta(minutes=119)
    assert evaluate_random_trigger(rule, now, last_fired=last_fired) is False


# ---------------------------------------------------------------------------
# Max 5 messages per day
# ---------------------------------------------------------------------------


def test_does_not_fire_when_daily_max_reached() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None, messages_today=5) is False


def test_fires_below_daily_max() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None, messages_today=4) is True


def test_fires_at_zero_messages_today() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None, messages_today=0) is True


def test_custom_max_per_day_respected() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None, messages_today=3, max_per_day=3) is False


def test_custom_max_per_day_below_limit() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None, messages_today=2, max_per_day=3) is True


# ---------------------------------------------------------------------------
# Disabled rule and wrong trigger type
# ---------------------------------------------------------------------------


def test_disabled_rule_does_not_fire() -> None:
    rule = _random_rule(enabled=False)
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is False


def test_time_based_rule_does_not_fire() -> None:
    rule = _random_rule(trigger_type=TriggerType.TIME_BASED)
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is False


def test_milestone_rule_does_not_fire() -> None:
    rule = _random_rule(trigger_type=TriggerType.MILESTONE)
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    assert evaluate_random_trigger(rule, now, last_fired=None) is False


# ---------------------------------------------------------------------------
# All constraints combine correctly
# ---------------------------------------------------------------------------


def test_all_constraints_pass() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 15, 0, tzinfo=UTC)
    last_fired = now - timedelta(hours=3)
    assert evaluate_random_trigger(rule, now, last_fired=last_fired, messages_today=2) is True


def test_gap_fails_even_when_all_else_passes() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 15, 0, tzinfo=UTC)
    last_fired = now - timedelta(minutes=30)  # too recent
    assert evaluate_random_trigger(rule, now, last_fired=last_fired, messages_today=2) is False


def test_max_fails_even_when_all_else_passes() -> None:
    rule = _random_rule()
    now = datetime(2026, 3, 23, 15, 0, tzinfo=UTC)
    last_fired = now - timedelta(hours=3)
    assert evaluate_random_trigger(rule, now, last_fired=last_fired, messages_today=5) is False

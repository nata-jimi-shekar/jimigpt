"""Tests for the trigger evaluation orchestrator."""

from datetime import datetime, timedelta, timezone

import pytest

from src.messaging.triggers import TriggerRule, TriggerType
from src.messaging.orchestrator import evaluate_triggers

UTC = timezone.utc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _time_rule(rule_id: str = "t1", cron: str = "0 8 * * *", **kwargs) -> TriggerRule:
    return TriggerRule(
        rule_id=rule_id,
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="entity-001",
        message_category="greeting",
        schedule_cron=cron,
        **kwargs,
    )


def _random_rule(rule_id: str = "r1", **kwargs) -> TriggerRule:
    return TriggerRule(
        rule_id=rule_id,
        trigger_type=TriggerType.RANDOM_INTERVAL,
        product="jimigpt",
        entity_id="entity-001",
        message_category="caring",
        window_start="09:00",
        window_end="21:00",
        **kwargs,
    )


def _ctx(
    timezone: str = "UTC",
    messages_today: int = 0,
    last_fired_by_rule: dict | None = None,
) -> dict:
    return {
        "timezone": timezone,
        "messages_today": messages_today,
        "last_fired_by_rule": last_fired_by_rule or {},
    }


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------


def test_empty_rules_returns_empty_list() -> None:
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([], now, _ctx())
    assert result == []


def test_returns_list_of_trigger_rules() -> None:
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx())
    assert isinstance(result, list)
    assert all(isinstance(r, TriggerRule) for r in result)


def test_no_rules_fire_returns_empty() -> None:
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 10, 0, tzinfo=UTC)  # wrong time
    result = evaluate_triggers([rule], now, _ctx())
    assert result == []


# ---------------------------------------------------------------------------
# TIME_BASED routing
# ---------------------------------------------------------------------------


def test_time_based_rule_fires_at_correct_time() -> None:
    rule = _time_rule(rule_id="t1", cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx())
    assert len(result) == 1
    assert result[0].rule_id == "t1"


def test_time_based_rule_excluded_at_wrong_time() -> None:
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 9, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx())
    assert result == []


def test_multiple_time_rules_only_matching_ones_fire() -> None:
    r1 = _time_rule(rule_id="t1", cron="0 8 * * *")
    r2 = _time_rule(rule_id="t2", cron="0 18 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([r1, r2], now, _ctx())
    assert len(result) == 1
    assert result[0].rule_id == "t1"


# ---------------------------------------------------------------------------
# RANDOM_INTERVAL routing
# ---------------------------------------------------------------------------


def test_random_rule_fires_within_window_no_last_fired() -> None:
    rule = _random_rule(rule_id="r1")
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx())
    assert len(result) == 1
    assert result[0].rule_id == "r1"


def test_random_rule_excluded_outside_window() -> None:
    rule = _random_rule(rule_id="r1")
    now = datetime(2026, 3, 23, 22, 0, tzinfo=UTC)  # after 21:00 window end
    result = evaluate_triggers([rule], now, _ctx())
    assert result == []


def test_random_rule_excluded_by_gap_from_context() -> None:
    rule = _random_rule(rule_id="r1")
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    last_fired = now - timedelta(minutes=30)
    ctx = _ctx(last_fired_by_rule={"r1": last_fired})
    result = evaluate_triggers([rule], now, ctx)
    assert result == []


def test_random_rule_fires_after_gap_from_context() -> None:
    rule = _random_rule(rule_id="r1")
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    last_fired = now - timedelta(hours=3)
    ctx = _ctx(last_fired_by_rule={"r1": last_fired})
    result = evaluate_triggers([rule], now, ctx)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# user_context keys
# ---------------------------------------------------------------------------


def test_timezone_from_context_used_for_time_trigger() -> None:
    # 8am cron evaluated in America/New_York (EDT = UTC-4)
    # 8am EDT = 12:00 UTC → passes at 12:00 UTC, not 08:00 UTC
    rule = _time_rule(cron="0 8 * * *")
    now_utc_8 = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    now_utc_12 = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)

    assert evaluate_triggers([rule], now_utc_8, _ctx(timezone="America/New_York")) == []
    assert len(evaluate_triggers([rule], now_utc_12, _ctx(timezone="America/New_York"))) == 1


def test_messages_today_from_context_counts_toward_cap() -> None:
    # 4 messages already sent; cap is 5; only 1 more should fire
    rules = [_random_rule(rule_id=f"r{i}") for i in range(3)]
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    ctx = _ctx(messages_today=4)
    result = evaluate_triggers(rules, now, ctx)
    assert len(result) == 1


def test_messages_today_at_cap_returns_empty() -> None:
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    ctx = _ctx(messages_today=5)
    result = evaluate_triggers([rule], now, ctx)
    assert result == []


def test_missing_context_keys_use_defaults() -> None:
    # Partial context — only timezone provided
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, {"timezone": "UTC"})
    assert len(result) == 1


def test_empty_context_uses_defaults() -> None:
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, {})
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Global daily cap (max 5 across all trigger types)
# ---------------------------------------------------------------------------


def test_global_cap_stops_at_five() -> None:
    # 6 random rules all eligible; only 5 should fire
    rules = [_random_rule(rule_id=f"r{i}") for i in range(6)]
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    result = evaluate_triggers(rules, now, _ctx(messages_today=0))
    assert len(result) == 5


def test_global_cap_applies_across_trigger_types() -> None:
    # 3 time-based (cron 12:00) + 3 random (window 08:00-21:00), all eligible at 12:00 → cap=5
    def _wide_random(rule_id: str) -> TriggerRule:
        return TriggerRule(
            rule_id=rule_id,
            trigger_type=TriggerType.RANDOM_INTERVAL,
            product="jimigpt",
            entity_id="entity-001",
            message_category="caring",
            window_start="08:00",
            window_end="21:00",
        )

    time_rules = [_time_rule(rule_id=f"t{i}", cron="0 12 * * *") for i in range(3)]
    rand_rules = [_wide_random(f"r{i}") for i in range(3)]
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    result = evaluate_triggers(time_rules + rand_rules, now, _ctx(messages_today=0))
    assert len(result) == 5


def test_cap_is_evaluated_incrementally() -> None:
    # messages_today=3; 4 eligible rules → only 2 more should fire
    rules = [_random_rule(rule_id=f"r{i}") for i in range(4)]
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    result = evaluate_triggers(rules, now, _ctx(messages_today=3))
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Disabled rules and unimplemented types
# ---------------------------------------------------------------------------


def test_disabled_rule_excluded() -> None:
    rule = _time_rule(cron="0 8 * * *", enabled=False)
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx())
    assert result == []


def test_event_based_rule_skipped_in_phase1() -> None:
    rule = TriggerRule(
        rule_id="e1",
        trigger_type=TriggerType.EVENT_BASED,
        product="jimigpt",
        entity_id="entity-001",
        message_category="need",
        event_type="feeding_time",
    )
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx())
    assert result == []


def test_milestone_rule_skipped_in_phase1() -> None:
    rule = TriggerRule(
        rule_id="m1",
        trigger_type=TriggerType.MILESTONE,
        product="jimigpt",
        entity_id="entity-001",
        message_category="celebrate",
    )
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx())
    assert result == []


def test_response_triggered_rule_skipped_in_phase1() -> None:
    rule = TriggerRule(
        rule_id="resp1",
        trigger_type=TriggerType.RESPONSE_TRIGGERED,
        product="jimigpt",
        entity_id="entity-001",
        message_category="caring",
    )
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx())
    assert result == []


def test_unimplemented_types_do_not_block_other_rules() -> None:
    # A skipped event-based rule doesn't prevent a valid time-based rule from firing
    event_rule = TriggerRule(
        rule_id="e1",
        trigger_type=TriggerType.EVENT_BASED,
        product="jimigpt",
        entity_id="entity-001",
        message_category="need",
        event_type="feeding_time",
    )
    time_rule = _time_rule(rule_id="t1", cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([event_rule, time_rule], now, _ctx())
    assert len(result) == 1
    assert result[0].rule_id == "t1"


# ---------------------------------------------------------------------------
# Foundation: sibling_entity_schedules (Phase 2 interface)
# ---------------------------------------------------------------------------


def test_none_sibling_entity_schedules_works() -> None:
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx(), sibling_entity_schedules=None)
    assert len(result) == 1


def test_empty_sibling_entity_schedules_works() -> None:
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    result = evaluate_triggers([rule], now, _ctx(), sibling_entity_schedules=[])
    assert len(result) == 1


def test_populated_sibling_entity_schedules_ignored_in_phase1() -> None:
    # Sibling schedule data present, but Phase 1 ignores it — behaviour unchanged
    rule = _time_rule(cron="0 8 * * *")
    now = datetime(2026, 3, 23, 8, 0, tzinfo=UTC)
    siblings = [
        {"entity_id": "entity-002", "entity_name": "Whiskers", "scheduled_messages": [], "last_message_at": None}
    ]
    result_without = evaluate_triggers([rule], now, _ctx(), sibling_entity_schedules=None)
    result_with = evaluate_triggers([rule], now, _ctx(), sibling_entity_schedules=siblings)
    assert result_without == result_with

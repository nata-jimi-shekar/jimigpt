"""Tests for trigger rule models and enums."""

import pytest
from pydantic import ValidationError

from src.messaging.triggers import TriggerRule, TriggerType


# ---------------------------------------------------------------------------
# TriggerType enum
# ---------------------------------------------------------------------------


def test_trigger_type_all_values_present() -> None:
    values = {t.value for t in TriggerType}
    assert "time_based" in values
    assert "event_based" in values
    assert "random" in values
    assert "response" in values
    assert "milestone" in values


def test_trigger_type_is_str_enum() -> None:
    assert TriggerType.TIME_BASED == "time_based"
    assert TriggerType.RANDOM_INTERVAL == "random"


# ---------------------------------------------------------------------------
# TriggerRule — required fields
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_rule() -> TriggerRule:
    return TriggerRule(
        rule_id="rule-001",
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="entity-abc",
        message_category="greeting",
    )


def test_trigger_rule_constructs(minimal_rule: TriggerRule) -> None:
    assert isinstance(minimal_rule, TriggerRule)


def test_trigger_rule_required_fields(minimal_rule: TriggerRule) -> None:
    assert minimal_rule.rule_id == "rule-001"
    assert minimal_rule.trigger_type == TriggerType.TIME_BASED
    assert minimal_rule.product == "jimigpt"
    assert minimal_rule.entity_id == "entity-abc"
    assert minimal_rule.message_category == "greeting"


def test_trigger_rule_missing_required_raises() -> None:
    with pytest.raises(ValidationError):
        TriggerRule(
            rule_id="rule-002",
            trigger_type=TriggerType.TIME_BASED,
            product="jimigpt",
            # entity_id and message_category missing
        )


# ---------------------------------------------------------------------------
# TriggerRule — defaults
# ---------------------------------------------------------------------------


def test_trigger_rule_timezone_defaults_to_utc(minimal_rule: TriggerRule) -> None:
    assert minimal_rule.timezone == "UTC"


def test_trigger_rule_enabled_defaults_true(minimal_rule: TriggerRule) -> None:
    assert minimal_rule.enabled is True


def test_trigger_rule_optional_fields_default_none(minimal_rule: TriggerRule) -> None:
    assert minimal_rule.schedule_cron is None
    assert minimal_rule.event_type is None
    assert minimal_rule.window_start is None
    assert minimal_rule.window_end is None


def test_trigger_rule_offset_minutes_defaults_zero(minimal_rule: TriggerRule) -> None:
    assert minimal_rule.offset_minutes == 0


# ---------------------------------------------------------------------------
# TriggerRule — all trigger types construct
# ---------------------------------------------------------------------------


def test_trigger_rule_time_based_with_cron() -> None:
    rule = TriggerRule(
        rule_id="r1",
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="e1",
        message_category="greeting",
        schedule_cron="0 8 * * *",
        timezone="America/New_York",
    )
    assert rule.schedule_cron == "0 8 * * *"
    assert rule.timezone == "America/New_York"


def test_trigger_rule_event_based() -> None:
    rule = TriggerRule(
        rule_id="r2",
        trigger_type=TriggerType.EVENT_BASED,
        product="jimigpt",
        entity_id="e1",
        message_category="need",
        event_type="feeding_time",
        offset_minutes=-30,
    )
    assert rule.event_type == "feeding_time"
    assert rule.offset_minutes == -30


def test_trigger_rule_random_interval_with_window() -> None:
    rule = TriggerRule(
        rule_id="r3",
        trigger_type=TriggerType.RANDOM_INTERVAL,
        product="jimigpt",
        entity_id="e1",
        message_category="caring",
        window_start="09:00",
        window_end="21:00",
    )
    assert rule.window_start == "09:00"
    assert rule.window_end == "21:00"


def test_trigger_rule_response_triggered() -> None:
    rule = TriggerRule(
        rule_id="r4",
        trigger_type=TriggerType.RESPONSE_TRIGGERED,
        product="jimigpt",
        entity_id="e1",
        message_category="caring",
    )
    assert rule.trigger_type == TriggerType.RESPONSE_TRIGGERED


def test_trigger_rule_milestone() -> None:
    rule = TriggerRule(
        rule_id="r5",
        trigger_type=TriggerType.MILESTONE,
        product="jimigpt",
        entity_id="e1",
        message_category="celebrate",
    )
    assert rule.trigger_type == TriggerType.MILESTONE


# ---------------------------------------------------------------------------
# Foundation fields — arc_template and sibling_entity_ids
# ---------------------------------------------------------------------------


def test_trigger_rule_arc_template_defaults_none(minimal_rule: TriggerRule) -> None:
    assert minimal_rule.arc_template is None


def test_trigger_rule_arc_template_can_be_set() -> None:
    rule = TriggerRule(
        rule_id="r6",
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="e1",
        message_category="greeting",
        arc_template="feeding_anticipation",
    )
    assert rule.arc_template == "feeding_anticipation"


def test_trigger_rule_sibling_entity_ids_defaults_empty(minimal_rule: TriggerRule) -> None:
    assert minimal_rule.sibling_entity_ids == []


def test_trigger_rule_sibling_entity_ids_can_be_set() -> None:
    rule = TriggerRule(
        rule_id="r7",
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="e1",
        message_category="greeting",
        sibling_entity_ids=["entity-dog", "entity-cat"],
    )
    assert rule.sibling_entity_ids == ["entity-dog", "entity-cat"]


def test_trigger_rule_foundation_fields_dont_affect_phase1_behavior(
    minimal_rule: TriggerRule,
) -> None:
    """Foundation fields at defaults produce a valid, enabled rule."""
    assert minimal_rule.enabled is True
    assert minimal_rule.arc_template is None
    assert minimal_rule.sibling_entity_ids == []

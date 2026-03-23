"""Tests for message intent selection engine."""

from datetime import datetime, timezone

import pytest

from src.messaging.models import MessageIntent
from src.messaging.signals import (
    ContextSignal,
    ContextSignalBundle,
    ContextSignalSource,
)
from src.messaging.intent import IntentProfile, TrustStage, select_intent
from src.messaging.triggers import TriggerRule, TriggerType

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bundle(signals: list[ContextSignal] | None = None) -> ContextSignalBundle:
    return ContextSignalBundle(
        signals=signals or [],
        user_id="u1",
        entity_id="e1",
        generated_at=datetime(2026, 3, 23, 10, 0, tzinfo=UTC),
    )


def _sig(key: str, value: str, source: ContextSignalSource = ContextSignalSource.TIME) -> ContextSignal:
    return ContextSignal(
        source=source,
        signal_key=key,
        signal_value=value,
        timestamp=datetime(2026, 3, 23, 10, 0, tzinfo=UTC),
    )


def _time_bundle(time_of_day: str = "morning", day_type: str = "workday") -> ContextSignalBundle:
    return _bundle([
        _sig("time_of_day", time_of_day),
        _sig("day_type", day_type),
    ])


def _rule(category: str = "greeting") -> TriggerRule:
    return TriggerRule(
        rule_id="t1",
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="entity-001",
        message_category=category,
        schedule_cron="0 8 * * *",
    )


def _random_rule(category: str = "caring") -> TriggerRule:
    return TriggerRule(
        rule_id="r1",
        trigger_type=TriggerType.RANDOM_INTERVAL,
        product="jimigpt",
        entity_id="entity-001",
        message_category=category,
        window_start="09:00",
        window_end="21:00",
    )


# Archetype weights: balanced (equal weight, sum to 1.0 across 14 intents)
_BALANCED_WEIGHTS: dict[str, float] = {intent.value: 1.0 / 14 for intent in MessageIntent}

# Archetype weights skewed toward playful (ENERGIZE, SURPRISE high)
_PLAYFUL_WEIGHTS: dict[str, float] = {intent.value: 0.02 for intent in MessageIntent}
_PLAYFUL_WEIGHTS.update({"energize": 0.40, "surprise": 0.36})


# ---------------------------------------------------------------------------
# TrustStage enum
# ---------------------------------------------------------------------------


def test_trust_stage_has_all_values() -> None:
    values = {s.value for s in TrustStage}
    assert "stranger" in values
    assert "initial" in values
    assert "working" in values
    assert "deep" in values
    assert "alliance" in values


# ---------------------------------------------------------------------------
# IntentProfile model
# ---------------------------------------------------------------------------


def test_intent_profile_constructs() -> None:
    profile = IntentProfile(
        primary_intent=MessageIntent.ENERGIZE,
        secondary_intent=None,
        intensity=0.7,
    )
    assert profile.primary_intent == MessageIntent.ENERGIZE
    assert profile.secondary_intent is None
    assert profile.intensity == 0.7


def test_intent_profile_secondary_intent_optional() -> None:
    profile = IntentProfile(
        primary_intent=MessageIntent.COMFORT,
        intensity=0.5,
    )
    assert profile.secondary_intent is None


def test_intent_profile_intensity_bounds() -> None:
    with pytest.raises(Exception):
        IntentProfile(primary_intent=MessageIntent.ENERGIZE, intensity=1.1)
    with pytest.raises(Exception):
        IntentProfile(primary_intent=MessageIntent.ENERGIZE, intensity=-0.1)


# ---------------------------------------------------------------------------
# select_intent — return type and structure
# ---------------------------------------------------------------------------


def test_select_intent_returns_intent_profile() -> None:
    result = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert isinstance(result, IntentProfile)
    assert isinstance(result.primary_intent, MessageIntent)
    assert 0.0 <= result.intensity <= 1.0


# ---------------------------------------------------------------------------
# Greeting category
# ---------------------------------------------------------------------------


def test_greeting_workday_morning_energize() -> None:
    """Morning workday greeting → ENERGIZE."""
    result = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(time_of_day="morning", day_type="workday"),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.ENERGIZE


def test_greeting_weekend_accompany() -> None:
    """Weekend greeting → ACCOMPANY (relaxed presence)."""
    result = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(time_of_day="morning", day_type="weekend"),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.ACCOMPANY


def test_greeting_early_morning_accompany() -> None:
    """Early morning (before 8am) → ACCOMPANY regardless of day type."""
    result = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(time_of_day="early_morning", day_type="workday"),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.ACCOMPANY


def test_greeting_late_night_accompany() -> None:
    result = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(time_of_day="late_night", day_type="workday"),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.ACCOMPANY


# ---------------------------------------------------------------------------
# Need / pet_need category
# ---------------------------------------------------------------------------


def test_need_category_selects_remind() -> None:
    result = select_intent(
        trigger=_rule("need"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.REMIND


def test_pet_need_category_selects_remind() -> None:
    result = select_intent(
        trigger=_rule("pet_need"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.REMIND


# ---------------------------------------------------------------------------
# Caring category
# ---------------------------------------------------------------------------


def test_caring_positive_sentiment_selects_affirm() -> None:
    signals = _bundle([
        _sig("time_of_day", "afternoon"),
        _sig("interaction:last_response_sentiment", "positive", ContextSignalSource.INTERACTION),
    ])
    result = select_intent(
        trigger=_random_rule("caring"),
        signals=signals,
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.AFFIRM


def test_caring_neutral_sentiment_selects_affirm() -> None:
    signals = _bundle([
        _sig("time_of_day", "afternoon"),
        _sig("interaction:last_response_sentiment", "neutral", ContextSignalSource.INTERACTION),
    ])
    result = select_intent(
        trigger=_random_rule("caring"),
        signals=signals,
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.AFFIRM


def test_caring_negative_sentiment_selects_comfort() -> None:
    signals = _bundle([
        _sig("time_of_day", "afternoon"),
        _sig("interaction:last_response_sentiment", "negative", ContextSignalSource.INTERACTION),
    ])
    result = select_intent(
        trigger=_random_rule("caring"),
        signals=signals,
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.COMFORT


def test_caring_no_sentiment_signal_defaults_to_affirm() -> None:
    """No interaction signals → default to AFFIRM."""
    result = select_intent(
        trigger=_random_rule("caring"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.AFFIRM


# ---------------------------------------------------------------------------
# Celebrate category
# ---------------------------------------------------------------------------


def test_celebrate_category_selects_celebrate() -> None:
    result = select_intent(
        trigger=_rule("celebrate"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.CELEBRATE


# ---------------------------------------------------------------------------
# Personality moment / surprise category
# ---------------------------------------------------------------------------


def test_personality_moment_playful_archetype_selects_energize_or_surprise() -> None:
    result = select_intent(
        trigger=_random_rule("personality_moment"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_PLAYFUL_WEIGHTS,
    )
    assert result.primary_intent in {MessageIntent.ENERGIZE, MessageIntent.SURPRISE}


# ---------------------------------------------------------------------------
# Negative sentiment modifier — cross-category
# ---------------------------------------------------------------------------


def test_negative_sentiment_shifts_greeting_toward_comfort() -> None:
    """Even a greeting shifts to COMFORT if sentiment is very negative."""
    signals = _bundle([
        _sig("time_of_day", "morning"),
        _sig("day_type", "workday"),
        _sig("interaction:last_response_sentiment", "negative", ContextSignalSource.INTERACTION),
    ])
    result = select_intent(
        trigger=_rule("greeting"),
        signals=signals,
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent == MessageIntent.COMFORT


# ---------------------------------------------------------------------------
# Anniversary signal → CELEBRATE or SURPRISE
# ---------------------------------------------------------------------------


def test_anniversary_signal_shifts_to_celebrate() -> None:
    signals = _bundle([
        _sig("time_of_day", "morning"),
        _sig("day_type", "workday"),
        _sig("seasonal:entity_anniversary", "true", ContextSignalSource.SEASONAL),
    ])
    result = select_intent(
        trigger=_rule("greeting"),
        signals=signals,
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.primary_intent in {MessageIntent.CELEBRATE, MessageIntent.SURPRISE}


# ---------------------------------------------------------------------------
# Trust stage → intensity
# ---------------------------------------------------------------------------


def test_stranger_trust_stage_has_lower_intensity() -> None:
    result_stranger = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(),
        trust_stage=TrustStage.STRANGER,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    result_working = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result_stranger.intensity < result_working.intensity


def test_deep_trust_has_higher_intensity_than_stranger() -> None:
    result_deep = select_intent(
        trigger=_rule("caring"),
        signals=_time_bundle(),
        trust_stage=TrustStage.DEEP,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    result_stranger = select_intent(
        trigger=_rule("caring"),
        signals=_time_bundle(),
        trust_stage=TrustStage.STRANGER,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result_deep.intensity > result_stranger.intensity


def test_stranger_intensity_at_most_point_four() -> None:
    result = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(),
        trust_stage=TrustStage.STRANGER,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    assert result.intensity <= 0.4


# ---------------------------------------------------------------------------
# Foundation: life_contexts parameter
# ---------------------------------------------------------------------------


def test_life_contexts_none_default_works() -> None:
    """Foundation: life_contexts=None accepted, no behavior change."""
    result = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
        life_contexts=None,
    )
    assert isinstance(result, IntentProfile)


def test_life_contexts_none_same_as_omitted() -> None:
    """Foundation: explicit None produces identical result to omitting the param."""
    base = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
    )
    with_none = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
        life_contexts=None,
    )
    assert base.primary_intent == with_none.primary_intent
    assert base.intensity == with_none.intensity


def test_life_contexts_empty_list_works() -> None:
    result = select_intent(
        trigger=_rule("greeting"),
        signals=_time_bundle(),
        trust_stage=TrustStage.WORKING,
        archetype_weights=_BALANCED_WEIGHTS,
        life_contexts=[],
    )
    assert isinstance(result, IntentProfile)

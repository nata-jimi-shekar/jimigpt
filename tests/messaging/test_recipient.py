"""Tests for recipient state inference."""

from datetime import datetime, timezone

import pytest

from src.messaging.intent import TrustStage
from src.messaging.signals import (
    ContextSignal,
    ContextSignalBundle,
    ContextSignalSource,
)
from src.messaging.recipient import RecipientState, TrustProfile, infer_recipient_state

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ts() -> datetime:
    return datetime(2026, 3, 23, 10, 0, tzinfo=UTC)


def _sig(
    key: str,
    value: str,
    source: ContextSignalSource = ContextSignalSource.TIME,
) -> ContextSignal:
    return ContextSignal(source=source, signal_key=key, signal_value=value, timestamp=_ts())


def _bundle(signals: list[ContextSignal] | None = None) -> ContextSignalBundle:
    return ContextSignalBundle(
        signals=signals or [],
        user_id="u1",
        entity_id="e1",
        generated_at=_ts(),
    )


def _trust(stage: TrustStage = TrustStage.WORKING) -> TrustProfile:
    return TrustProfile(
        user_id="u1",
        entity_id="e1",
        current_stage=stage,
        stage_entered_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _time_bundle(time_of_day: str, day_type: str = "workday") -> ContextSignalBundle:
    return _bundle([
        _sig("time_of_day", time_of_day),
        _sig("day_type", day_type),
    ])


def _interaction_sig(key: str, value: str) -> ContextSignal:
    return _sig(key, value, source=ContextSignalSource.INTERACTION)


def _seasonal_sig(key: str, value: str) -> ContextSignal:
    return _sig(key, value, source=ContextSignalSource.SEASONAL)


# ---------------------------------------------------------------------------
# TrustProfile model
# ---------------------------------------------------------------------------


def test_trust_profile_constructs() -> None:
    tp = TrustProfile(
        user_id="u1",
        entity_id="e1",
        current_stage=TrustStage.WORKING,
        stage_entered_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert tp.current_stage == TrustStage.WORKING
    assert tp.user_id == "u1"


# ---------------------------------------------------------------------------
# RecipientState model
# ---------------------------------------------------------------------------


def test_recipient_state_constructs() -> None:
    state = RecipientState(
        likely_availability="free",
        likely_energy=0.7,
        likely_receptivity=0.8,
        emotional_context="neutral",
        state_confidence=0.5,
    )
    assert state.likely_availability == "free"
    assert state.likely_energy == 0.7


def test_recipient_state_field_bounds() -> None:
    with pytest.raises(Exception):
        RecipientState(
            likely_availability="free",
            likely_energy=1.1,
            likely_receptivity=0.5,
            emotional_context="neutral",
            state_confidence=0.5,
        )
    with pytest.raises(Exception):
        RecipientState(
            likely_availability="free",
            likely_energy=0.5,
            likely_receptivity=-0.1,
            emotional_context="neutral",
            state_confidence=0.5,
        )


# ---------------------------------------------------------------------------
# infer_recipient_state — return type
# ---------------------------------------------------------------------------


def test_infer_returns_recipient_state() -> None:
    result = infer_recipient_state(
        signals=_bundle(),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert isinstance(result, RecipientState)


# ---------------------------------------------------------------------------
# Workday morning → busy, low receptivity
# ---------------------------------------------------------------------------


def test_workday_morning_availability_busy() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("morning", "workday"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_availability == "busy"


def test_workday_morning_receptivity_low() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("morning", "workday"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_receptivity < 0.5


def test_workday_midday_availability_busy() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("midday", "workday"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_availability == "busy"


def test_workday_afternoon_availability_busy() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("afternoon", "workday"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_availability == "busy"


# ---------------------------------------------------------------------------
# Weekend → free, high receptivity
# ---------------------------------------------------------------------------


def test_weekend_availability_free() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("morning", "weekend"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_availability == "free"


def test_weekend_receptivity_high() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("morning", "weekend"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_receptivity >= 0.7


def test_weekend_likely_energy_higher_than_workday_morning() -> None:
    weekend = infer_recipient_state(
        signals=_time_bundle("morning", "weekend"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    workday = infer_recipient_state(
        signals=_time_bundle("morning", "workday"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert weekend.likely_energy >= workday.likely_energy


# ---------------------------------------------------------------------------
# Late night / sleeping
# ---------------------------------------------------------------------------


def test_late_night_availability_sleeping() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("late_night"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_availability == "sleeping"


def test_late_night_low_energy() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("late_night"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_energy <= 0.3


# ---------------------------------------------------------------------------
# Evening → free, winding down
# ---------------------------------------------------------------------------


def test_evening_availability_free() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("evening"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.likely_availability == "free"


# ---------------------------------------------------------------------------
# Recent negative reply → stressed
# ---------------------------------------------------------------------------


def test_negative_sentiment_emotional_context_stressed() -> None:
    signals = _bundle([
        _sig("time_of_day", "afternoon"),
        _sig("day_type", "workday"),
        _interaction_sig("interaction:last_response_sentiment", "negative"),
    ])
    result = infer_recipient_state(
        signals=signals,
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.emotional_context == "stressed"


def test_positive_sentiment_emotional_context_positive() -> None:
    signals = _bundle([
        _sig("time_of_day", "afternoon"),
        _sig("day_type", "workday"),
        _interaction_sig("interaction:last_response_sentiment", "positive"),
    ])
    result = infer_recipient_state(
        signals=signals,
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.emotional_context == "positive"


# ---------------------------------------------------------------------------
# Long silence → lonely
# ---------------------------------------------------------------------------


def test_long_silence_emotional_context_lonely() -> None:
    """days_since_last_reply > 3 → lonely."""
    signals = _bundle([
        _sig("time_of_day", "afternoon"),
        _interaction_sig("interaction:days_since_last_reply", "5"),
    ])
    result = infer_recipient_state(
        signals=signals,
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.emotional_context == "lonely"


def test_recent_reply_not_lonely() -> None:
    signals = _bundle([
        _sig("time_of_day", "afternoon"),
        _interaction_sig("interaction:days_since_last_reply", "1"),
    ])
    result = infer_recipient_state(
        signals=signals,
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.emotional_context != "lonely"


def test_negative_sentiment_beats_silence_for_emotional_context() -> None:
    """Negative sentiment takes priority over long silence."""
    signals = _bundle([
        _interaction_sig("interaction:last_response_sentiment", "negative"),
        _interaction_sig("interaction:days_since_last_reply", "5"),
    ])
    result = infer_recipient_state(
        signals=signals,
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.emotional_context == "stressed"


# ---------------------------------------------------------------------------
# Anniversary → celebratory
# ---------------------------------------------------------------------------


def test_anniversary_emotional_context_celebratory() -> None:
    signals = _bundle([
        _sig("time_of_day", "morning"),
        _seasonal_sig("seasonal:entity_anniversary", "true"),
    ])
    result = infer_recipient_state(
        signals=signals,
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.emotional_context == "celebratory"


# ---------------------------------------------------------------------------
# No signals → neutral defaults
# ---------------------------------------------------------------------------


def test_no_signals_returns_neutral_defaults() -> None:
    result = infer_recipient_state(
        signals=_bundle(),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.emotional_context == "neutral"
    assert result.likely_availability == "free"
    assert 0.0 <= result.likely_energy <= 1.0
    assert 0.0 <= result.likely_receptivity <= 1.0


# ---------------------------------------------------------------------------
# State confidence = signal coverage
# ---------------------------------------------------------------------------


def test_confidence_zero_with_no_signals() -> None:
    result = infer_recipient_state(
        signals=_bundle(),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.state_confidence == 0.0


def test_confidence_increases_with_more_signal_sources() -> None:
    time_only = infer_recipient_state(
        signals=_time_bundle("morning"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    with_interaction = infer_recipient_state(
        signals=_bundle([
            _sig("time_of_day", "morning"),
            _sig("day_type", "workday"),
            _interaction_sig("interaction:last_response_sentiment", "positive"),
        ]),
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert with_interaction.state_confidence > time_only.state_confidence


def test_confidence_at_most_one() -> None:
    signals = _bundle([
        _sig("time_of_day", "morning"),
        _sig("day_type", "workday"),
        _interaction_sig("interaction:last_response_sentiment", "positive"),
        _interaction_sig("interaction:days_since_last_reply", "1"),
        _seasonal_sig("seasonal:season", "spring"),
        _seasonal_sig("seasonal:entity_anniversary", "false"),
    ])
    result = infer_recipient_state(
        signals=signals,
        trust_profile=_trust(),
        interaction_history=[],
    )
    assert result.state_confidence <= 1.0


# ---------------------------------------------------------------------------
# Foundation: life_contexts parameter
# ---------------------------------------------------------------------------


def test_life_contexts_none_default_accepted() -> None:
    result = infer_recipient_state(
        signals=_time_bundle("morning"),
        trust_profile=_trust(),
        interaction_history=[],
        life_contexts=None,
    )
    assert isinstance(result, RecipientState)


def test_life_contexts_none_same_as_omitted() -> None:
    base = infer_recipient_state(
        signals=_time_bundle("morning"),
        trust_profile=_trust(),
        interaction_history=[],
    )
    with_none = infer_recipient_state(
        signals=_time_bundle("morning"),
        trust_profile=_trust(),
        interaction_history=[],
        life_contexts=None,
    )
    assert base.likely_availability == with_none.likely_availability
    assert base.emotional_context == with_none.emotional_context
    assert base.state_confidence == with_none.state_confidence


def test_life_contexts_empty_list_accepted() -> None:
    result = infer_recipient_state(
        signals=_bundle(),
        trust_profile=_trust(),
        interaction_history=[],
        life_contexts=[],
    )
    assert isinstance(result, RecipientState)

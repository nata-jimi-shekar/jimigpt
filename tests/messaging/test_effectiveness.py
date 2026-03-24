"""Tests for message effectiveness tracking and scoring."""

from datetime import datetime, timezone

import pytest

from src.messaging.models import MessageIntent
from src.personality.models import ToneSpectrum
from src.messaging.effectiveness import (
    MessageEffectiveness,
    record_effectiveness,
    score_effectiveness,
)

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ts() -> datetime:
    return datetime(2026, 3, 23, 10, 0, tzinfo=UTC)


def _tone() -> ToneSpectrum:
    return ToneSpectrum(
        warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
    )


def _make(
    user_reaction: str | None = None,
    user_replied: bool = False,
    reply_sentiment: str | None = None,
    time_to_reaction_seconds: int | None = None,
    effectiveness_score: float = 0.0,
) -> MessageEffectiveness:
    return MessageEffectiveness(
        message_id="m1",
        intended_intent=MessageIntent.ENERGIZE,
        intended_tone=_tone(),
        user_reaction=user_reaction,
        user_replied=user_replied,
        reply_sentiment=reply_sentiment,
        time_to_reaction_seconds=time_to_reaction_seconds,
        effectiveness_score=effectiveness_score,
    )


# ---------------------------------------------------------------------------
# MessageEffectiveness model
# ---------------------------------------------------------------------------


def test_message_effectiveness_constructs() -> None:
    eff = _make(effectiveness_score=0.5)
    assert eff.message_id == "m1"
    assert eff.intended_intent == MessageIntent.ENERGIZE
    assert eff.effectiveness_score == 0.5


def test_message_effectiveness_all_fields_optional_nullable() -> None:
    eff = _make()
    assert eff.user_reaction is None
    assert eff.user_replied is False
    assert eff.reply_sentiment is None
    assert eff.time_to_reaction_seconds is None


def test_effectiveness_score_bounds_enforced() -> None:
    with pytest.raises(Exception):
        _make(effectiveness_score=1.1)
    with pytest.raises(Exception):
        _make(effectiveness_score=-0.1)


def test_effectiveness_score_zero_is_valid() -> None:
    eff = _make(effectiveness_score=0.0)
    assert eff.effectiveness_score == 0.0


def test_effectiveness_score_one_is_valid() -> None:
    eff = _make(effectiveness_score=1.0)
    assert eff.effectiveness_score == 1.0


# ---------------------------------------------------------------------------
# score_effectiveness — individual components
# ---------------------------------------------------------------------------


def test_score_no_reaction_no_reply_no_sentiment_is_zero() -> None:
    score = score_effectiveness(
        user_reaction=None,
        user_replied=False,
        reply_sentiment=None,
    )
    assert score == 0.0


def test_score_positive_reaction_adds_point_three() -> None:
    score = score_effectiveness(
        user_reaction="positive",
        user_replied=False,
        reply_sentiment=None,
    )
    assert score == pytest.approx(0.3)


def test_score_reply_adds_point_two() -> None:
    score = score_effectiveness(
        user_reaction=None,
        user_replied=True,
        reply_sentiment=None,
    )
    assert score == pytest.approx(0.2)


def test_score_positive_sentiment_adds_point_two() -> None:
    score = score_effectiveness(
        user_reaction=None,
        user_replied=True,
        reply_sentiment="positive",
    )
    assert score == pytest.approx(0.4)


def test_score_all_three_components_max_point_seven() -> None:
    score = score_effectiveness(
        user_reaction="positive",
        user_replied=True,
        reply_sentiment="positive",
    )
    assert score == pytest.approx(0.7)


def test_score_negative_reaction_does_not_increase_score() -> None:
    score = score_effectiveness(
        user_reaction="negative",
        user_replied=False,
        reply_sentiment=None,
    )
    assert score == pytest.approx(0.0)


def test_score_neutral_sentiment_does_not_increase_score() -> None:
    score = score_effectiveness(
        user_reaction=None,
        user_replied=True,
        reply_sentiment="neutral",
    )
    assert score == pytest.approx(0.2)


def test_score_reply_without_positive_sentiment_no_sentiment_bonus() -> None:
    score = score_effectiveness(
        user_reaction=None,
        user_replied=True,
        reply_sentiment="negative",
    )
    assert score == pytest.approx(0.2)


def test_score_positive_reaction_and_reply_no_sentiment() -> None:
    score = score_effectiveness(
        user_reaction="positive",
        user_replied=True,
        reply_sentiment=None,
    )
    assert score == pytest.approx(0.5)


def test_score_positive_reaction_and_positive_sentiment_no_reply() -> None:
    # sentiment bonus only applies when user_replied=True (they replied with positive sentiment)
    # reaction + sentiment without a reply = 0.3 + 0.2
    score = score_effectiveness(
        user_reaction="positive",
        user_replied=False,
        reply_sentiment="positive",
    )
    # reply_sentiment without a reply is logically inconsistent but should score
    # whatever the system allows; we just verify the total is <= 0.7
    assert 0.0 <= score <= 0.7


def test_score_always_in_valid_range() -> None:
    for reaction in ["positive", "negative", None]:
        for replied in [True, False]:
            for sentiment in ["positive", "neutral", "negative", None]:
                score = score_effectiveness(reaction, replied, sentiment)
                assert 0.0 <= score <= 1.0, (
                    f"Out of range for reaction={reaction}, "
                    f"replied={replied}, sentiment={sentiment}: {score}"
                )


# ---------------------------------------------------------------------------
# record_effectiveness — factory function
# ---------------------------------------------------------------------------


def test_record_effectiveness_returns_message_effectiveness() -> None:
    result = record_effectiveness(
        message_id="m42",
        intended_intent=MessageIntent.COMFORT,
        intended_tone=_tone(),
        user_reaction="positive",
        user_replied=True,
        reply_sentiment="positive",
        time_to_reaction_seconds=45,
    )
    assert isinstance(result, MessageEffectiveness)


def test_record_effectiveness_computes_score_automatically() -> None:
    result = record_effectiveness(
        message_id="m1",
        intended_intent=MessageIntent.ENERGIZE,
        intended_tone=_tone(),
        user_reaction="positive",
        user_replied=True,
        reply_sentiment="positive",
        time_to_reaction_seconds=None,
    )
    assert result.effectiveness_score == pytest.approx(0.7)


def test_record_effectiveness_no_response_score_zero() -> None:
    result = record_effectiveness(
        message_id="m1",
        intended_intent=MessageIntent.ENERGIZE,
        intended_tone=_tone(),
        user_reaction=None,
        user_replied=False,
        reply_sentiment=None,
        time_to_reaction_seconds=None,
    )
    assert result.effectiveness_score == 0.0


def test_record_effectiveness_preserves_message_id() -> None:
    result = record_effectiveness(
        message_id="unique-123",
        intended_intent=MessageIntent.AFFIRM,
        intended_tone=_tone(),
        user_reaction=None,
        user_replied=False,
        reply_sentiment=None,
        time_to_reaction_seconds=None,
    )
    assert result.message_id == "unique-123"


def test_record_effectiveness_preserves_intent() -> None:
    result = record_effectiveness(
        message_id="m1",
        intended_intent=MessageIntent.CELEBRATE,
        intended_tone=_tone(),
        user_reaction=None,
        user_replied=False,
        reply_sentiment=None,
        time_to_reaction_seconds=None,
    )
    assert result.intended_intent == MessageIntent.CELEBRATE


def test_record_effectiveness_preserves_tone() -> None:
    tone = _tone()
    result = record_effectiveness(
        message_id="m1",
        intended_intent=MessageIntent.ENERGIZE,
        intended_tone=tone,
        user_reaction=None,
        user_replied=False,
        reply_sentiment=None,
        time_to_reaction_seconds=None,
    )
    assert result.intended_tone == tone


def test_record_effectiveness_stores_time_to_reaction() -> None:
    result = record_effectiveness(
        message_id="m1",
        intended_intent=MessageIntent.ENERGIZE,
        intended_tone=_tone(),
        user_reaction="positive",
        user_replied=False,
        reply_sentiment=None,
        time_to_reaction_seconds=120,
    )
    assert result.time_to_reaction_seconds == 120


def test_record_effectiveness_from_generated_message() -> None:
    """Can build effectiveness directly from GeneratedMessage fields."""
    from src.messaging.generator import GeneratedMessage

    msg = GeneratedMessage(
        message_id="gen-1",
        entity_id="e1",
        content="Good morning!",
        generated_at=_ts(),
        model_used="claude-sonnet-4-6",
        prompt_tokens=100,
        completion_tokens=8,
        message_category="greeting",
        intended_intent=MessageIntent.ENERGIZE,
        intended_tone=_tone(),
        character_count=13,
    )
    result = record_effectiveness(
        message_id=msg.message_id,
        intended_intent=msg.intended_intent,
        intended_tone=msg.intended_tone,
        user_reaction="positive",
        user_replied=False,
        reply_sentiment=None,
        time_to_reaction_seconds=None,
    )
    assert result.message_id == "gen-1"
    assert result.effectiveness_score == pytest.approx(0.3)

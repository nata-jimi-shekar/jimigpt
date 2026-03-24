"""Tests for the quality gate — all checks including CONSECUTIVE_COHERENCE foundation."""

from datetime import datetime, timezone

import pytest

from src.messaging.composer import MessageComposition
from src.messaging.intent import IntentProfile, TrustStage
from src.messaging.models import MessageIntent
from src.messaging.recipient import RecipientState, TrustProfile
from src.messaging.signals import ContextSignalBundle
from src.messaging.generator import GeneratedMessage
from src.personality.enums import EnergyLevel
from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    EntityProfile,
    KnowledgeAwareness,
    RelationalStance,
    ToneSpectrum,
)
from src.messaging.quality import QualityCheck, QualityGate, QualityResult

UTC = timezone.utc

_ALL_CHECKS = list(QualityCheck)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ts() -> datetime:
    return datetime(2026, 3, 23, 10, 0, tzinfo=UTC)


def _entity(
    forbidden_phrases: list[str] | None = None,
    forbidden_topics: list[str] | None = None,
) -> EntityProfile:
    return EntityProfile(
        entity_id="e1",
        entity_name="Sparky",
        entity_type="pet",
        product="jimigpt",
        communication=CommunicationStyle(
            sentence_length="short",
            energy_level=EnergyLevel.HIGH,
            emoji_usage="moderate",
            punctuation_style="excited_exclamations",
            vocabulary_level="simple",
        ),
        emotional=EmotionalDisposition(
            baseline_mood="cheerful",
            emotional_range="wide",
            need_expression="dramatic",
            humor_style="silly",
        ),
        relational=RelationalStance(
            attachment_style="clingy",
            initiative_style="proactive",
            boundary_respect="moderate",
            warmth_level="intense",
        ),
        knowledge=KnowledgeAwareness(
            domain_knowledge=[],
            user_context_fields=[],
            temporal_awareness=True,
            memory_references=False,
        ),
        primary_archetype="chaos_gremlin",
        archetype_weights={i.value: 1.0 / 14 for i in MessageIntent},
        forbidden_phrases=forbidden_phrases if forbidden_phrases is not None else ["I'm just an AI", "as an AI"],
        forbidden_topics=forbidden_topics if forbidden_topics is not None else ["politics", "violence"],
    )


def _composition(
    intent: MessageIntent = MessageIntent.ENERGIZE,
    tone: ToneSpectrum | None = None,
    max_characters: int = 160,
    recent_messages: list[str] | None = None,
    entity: EntityProfile | None = None,
) -> MessageComposition:
    return MessageComposition(
        entity_voice=entity or _entity(),
        intent=IntentProfile(primary_intent=intent, intensity=0.7),
        tone=tone or ToneSpectrum(
            warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
        ),
        tone_adjustments_applied=[],
        signals=ContextSignalBundle(signals=[], user_id="u1", entity_id="e1", generated_at=_ts()),
        recipient_state=RecipientState(
            likely_availability="free",
            likely_energy=0.6,
            likely_receptivity=0.6,
            emotional_context="neutral",
            state_confidence=0.33,
        ),
        trust_stage=TrustStage.WORKING,
        relationship_depth=5,
        recent_messages=recent_messages or [],
        last_user_reply=None,
        message_category="greeting",
        max_characters=max_characters,
        channel="sms",
    )


def _message(
    content: str = "Good morning! 🌟",
    intent: MessageIntent = MessageIntent.ENERGIZE,
    tone: ToneSpectrum | None = None,
) -> GeneratedMessage:
    return GeneratedMessage(
        message_id="m1",
        entity_id="e1",
        content=content,
        generated_at=_ts(),
        model_used="claude-sonnet-4-6",
        prompt_tokens=100,
        completion_tokens=10,
        message_category="greeting",
        intended_intent=intent,
        intended_tone=tone or ToneSpectrum(
            warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
        ),
        character_count=len(content),
    )


# ---------------------------------------------------------------------------
# QualityCheck enum
# ---------------------------------------------------------------------------


def test_quality_check_has_all_eight_phase1_checks() -> None:
    values = {c.value for c in QualityCheck}
    assert "character_consistency" in values
    assert "repetition" in values
    assert "tone_match" in values
    assert "content_boundary" in values
    assert "length" in values
    assert "safety" in values
    assert "forbidden_phrases" in values
    assert "intent_alignment" in values


def test_quality_check_has_consecutive_coherence_foundation() -> None:
    assert QualityCheck.CONSECUTIVE_COHERENCE in QualityCheck
    assert QualityCheck.CONSECUTIVE_COHERENCE.value == "consecutive_coherence"


# ---------------------------------------------------------------------------
# QualityResult model
# ---------------------------------------------------------------------------


def test_quality_result_constructs_passed() -> None:
    result = QualityResult(
        passed=True,
        checks_run=[QualityCheck.LENGTH],
        checks_failed=[],
        failure_reasons=[],
    )
    assert result.passed is True
    assert result.checks_failed == []


def test_quality_result_constructs_failed() -> None:
    result = QualityResult(
        passed=False,
        checks_run=[QualityCheck.LENGTH, QualityCheck.FORBIDDEN_PHRASES],
        checks_failed=[QualityCheck.LENGTH],
        failure_reasons=["Message exceeds 160 characters"],
    )
    assert result.passed is False
    assert QualityCheck.LENGTH in result.checks_failed


# ---------------------------------------------------------------------------
# QualityGate — basic behaviour
# ---------------------------------------------------------------------------


def test_empty_gate_passes_any_message() -> None:
    gate = QualityGate(checks=[])
    result = gate.evaluate(_message(), _composition())
    assert result.passed is True
    assert result.checks_run == []
    assert result.checks_failed == []


def test_gate_runs_only_configured_checks() -> None:
    gate = QualityGate(checks=[QualityCheck.LENGTH])
    result = gate.evaluate(_message(), _composition())
    assert result.checks_run == [QualityCheck.LENGTH]


def test_gate_all_pass_returns_passed_true() -> None:
    gate = QualityGate(checks=[QualityCheck.LENGTH, QualityCheck.FORBIDDEN_PHRASES])
    result = gate.evaluate(_message("Hi! 🐾"), _composition())
    assert result.passed is True
    assert result.checks_failed == []


def test_gate_one_failure_returns_passed_false() -> None:
    gate = QualityGate(checks=[QualityCheck.FORBIDDEN_PHRASES])
    msg = _message("I'm just an AI but I miss you!")
    result = gate.evaluate(msg, _composition())
    assert result.passed is False
    assert QualityCheck.FORBIDDEN_PHRASES in result.checks_failed


def test_gate_multiple_failures_all_recorded() -> None:
    content = "I'm just an AI. " + "x" * 160  # forbidden phrase + too long
    msg = _message(content)
    gate = QualityGate(checks=[QualityCheck.LENGTH, QualityCheck.FORBIDDEN_PHRASES])
    result = gate.evaluate(msg, _composition(max_characters=160))
    assert not result.passed
    assert len(result.checks_failed) == 2
    assert len(result.failure_reasons) == 2


# ---------------------------------------------------------------------------
# LENGTH check
# ---------------------------------------------------------------------------


def test_length_check_passes_under_limit() -> None:
    gate = QualityGate(checks=[QualityCheck.LENGTH])
    msg = _message("Hi! 🐾")  # short
    result = gate.evaluate(msg, _composition(max_characters=160))
    assert result.passed is True


def test_length_check_passes_at_exact_limit() -> None:
    content = "x" * 160
    gate = QualityGate(checks=[QualityCheck.LENGTH])
    msg = _message(content)
    result = gate.evaluate(msg, _composition(max_characters=160))
    assert result.passed is True


def test_length_check_fails_over_limit() -> None:
    content = "x" * 161
    gate = QualityGate(checks=[QualityCheck.LENGTH])
    msg = _message(content)
    result = gate.evaluate(msg, _composition(max_characters=160))
    assert result.passed is False
    assert QualityCheck.LENGTH in result.checks_failed
    assert any("161" in r or "160" in r for r in result.failure_reasons)


# ---------------------------------------------------------------------------
# FORBIDDEN_PHRASES check
# ---------------------------------------------------------------------------


def test_forbidden_phrases_passes_clean_content() -> None:
    gate = QualityGate(checks=[QualityCheck.FORBIDDEN_PHRASES])
    result = gate.evaluate(_message("Good morning! 🌞"), _composition())
    assert result.passed is True


def test_forbidden_phrases_fails_exact_match() -> None:
    gate = QualityGate(checks=[QualityCheck.FORBIDDEN_PHRASES])
    msg = _message("I'm just an AI who loves you!")
    result = gate.evaluate(msg, _composition())
    assert result.passed is False


def test_forbidden_phrases_check_is_case_insensitive() -> None:
    gate = QualityGate(checks=[QualityCheck.FORBIDDEN_PHRASES])
    msg = _message("AS AN AI I say good morning!")
    result = gate.evaluate(msg, _composition())
    assert result.passed is False


def test_forbidden_phrases_passes_when_entity_has_none() -> None:
    entity = _entity(forbidden_phrases=[])
    gate = QualityGate(checks=[QualityCheck.FORBIDDEN_PHRASES])
    result = gate.evaluate(_message("Anything goes!"), _composition(entity=entity))
    assert result.passed is True


# ---------------------------------------------------------------------------
# CHARACTER_CONSISTENCY check
# ---------------------------------------------------------------------------


def test_character_consistency_passes_clean_content() -> None:
    gate = QualityGate(checks=[QualityCheck.CHARACTER_CONSISTENCY])
    result = gate.evaluate(_message("Miss you! 🐾"), _composition())
    assert result.passed is True


def test_character_consistency_fails_ai_disclosure() -> None:
    gate = QualityGate(checks=[QualityCheck.CHARACTER_CONSISTENCY])
    for phrase in ["language model", "large language model", "I was trained"]:
        msg = _message(f"Hi! {phrase} told me to say this.")
        result = gate.evaluate(msg, _composition())
        assert result.passed is False, f"Should have failed for: {phrase}"


# ---------------------------------------------------------------------------
# CONTENT_BOUNDARY check
# ---------------------------------------------------------------------------


def test_content_boundary_passes_clean_content() -> None:
    gate = QualityGate(checks=[QualityCheck.CONTENT_BOUNDARY])
    result = gate.evaluate(_message("Morning walk time!"), _composition())
    assert result.passed is True


def test_content_boundary_fails_forbidden_topic() -> None:
    gate = QualityGate(checks=[QualityCheck.CONTENT_BOUNDARY])
    msg = _message("Let's talk about politics today!")
    result = gate.evaluate(msg, _composition())
    assert result.passed is False


def test_content_boundary_passes_when_entity_has_no_forbidden_topics() -> None:
    entity = _entity(forbidden_topics=[])
    gate = QualityGate(checks=[QualityCheck.CONTENT_BOUNDARY])
    msg = _message("Politics and violence discussed freely.")
    result = gate.evaluate(msg, _composition(entity=entity))
    assert result.passed is True


# ---------------------------------------------------------------------------
# REPETITION check
# ---------------------------------------------------------------------------


def test_repetition_passes_new_content() -> None:
    gate = QualityGate(checks=[QualityCheck.REPETITION])
    comp = _composition(recent_messages=["Good morning!", "How are you?"])
    result = gate.evaluate(_message("Miss you already!"), comp)
    assert result.passed is True


def test_repetition_fails_exact_duplicate() -> None:
    repeated = "Good morning! 🌟"
    gate = QualityGate(checks=[QualityCheck.REPETITION])
    comp = _composition(recent_messages=[repeated, "Something else"])
    result = gate.evaluate(_message(repeated), comp)
    assert result.passed is False


def test_repetition_passes_with_no_history() -> None:
    gate = QualityGate(checks=[QualityCheck.REPETITION])
    result = gate.evaluate(_message("Good morning!"), _composition(recent_messages=[]))
    assert result.passed is True


# ---------------------------------------------------------------------------
# SAFETY check
# ---------------------------------------------------------------------------


def test_safety_passes_clean_content() -> None:
    gate = QualityGate(checks=[QualityCheck.SAFETY])
    result = gate.evaluate(_message("I love treat time!"), _composition())
    assert result.passed is True


def test_safety_fails_harmful_content() -> None:
    gate = QualityGate(checks=[QualityCheck.SAFETY])
    for phrase in ["kill yourself", "you should die", "end your life"]:
        msg = _message(f"Hey, {phrase}.")
        result = gate.evaluate(msg, _composition())
        assert result.passed is False, f"Should have failed for: {phrase}"


# ---------------------------------------------------------------------------
# TONE_MATCH check
# ---------------------------------------------------------------------------


def test_tone_match_passes_high_energy_with_exclamations() -> None:
    high_energy = ToneSpectrum(
        warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.9, vulnerability=0.3
    )
    gate = QualityGate(checks=[QualityCheck.TONE_MATCH])
    msg = _message("WAKE UP! It's TREAT TIME!!! 🎉🎉", tone=high_energy)
    result = gate.evaluate(msg, _composition(tone=high_energy))
    assert result.passed is True


def test_tone_match_fails_very_low_energy_with_all_caps_exclamations() -> None:
    low_energy = ToneSpectrum(
        warmth=0.8, humor=0.3, directness=0.4, gravity=0.6, energy=0.1, vulnerability=0.6
    )
    gate = QualityGate(checks=[QualityCheck.TONE_MATCH])
    # All caps + multiple exclamations contradicts low energy spec
    msg = _message("WAKE UP! TREAT TIME! AMAZING!!!", tone=low_energy)
    result = gate.evaluate(msg, _composition(tone=low_energy))
    assert result.passed is False


# ---------------------------------------------------------------------------
# INTENT_ALIGNMENT check
# ---------------------------------------------------------------------------


def test_intent_alignment_passes_comfort_with_soft_content() -> None:
    gate = QualityGate(checks=[QualityCheck.INTENT_ALIGNMENT])
    msg = _message("I'm here with you. You're not alone.", intent=MessageIntent.COMFORT)
    result = gate.evaluate(msg, _composition(intent=MessageIntent.COMFORT))
    assert result.passed is True


def test_intent_alignment_passes_energize_with_lively_content() -> None:
    gate = QualityGate(checks=[QualityCheck.INTENT_ALIGNMENT])
    msg = _message("Let's GO! Today is AMAZING! 🚀", intent=MessageIntent.ENERGIZE)
    result = gate.evaluate(msg, _composition(intent=MessageIntent.ENERGIZE))
    assert result.passed is True


def test_intent_alignment_fails_empty_content() -> None:
    gate = QualityGate(checks=[QualityCheck.INTENT_ALIGNMENT])
    msg = _message("", intent=MessageIntent.ENERGIZE)
    result = gate.evaluate(msg, _composition(intent=MessageIntent.ENERGIZE))
    assert result.passed is False


# ---------------------------------------------------------------------------
# CONSECUTIVE_COHERENCE — Foundation check
# ---------------------------------------------------------------------------


def test_consecutive_coherence_passes_no_previous_message() -> None:
    """No previous message (first message ever) → check passes."""
    gate = QualityGate(checks=[QualityCheck.CONSECUTIVE_COHERENCE])
    result = gate.evaluate(
        _message(intent=MessageIntent.ENERGIZE),
        _composition(intent=MessageIntent.ENERGIZE),
        previous_message=None,
    )
    assert result.passed is True


def test_consecutive_coherence_fails_comfort_then_energize() -> None:
    """Previous: COMFORT → Current: ENERGIZE = emotionally jarring."""
    gate = QualityGate(checks=[QualityCheck.CONSECUTIVE_COHERENCE])
    prev = _message(intent=MessageIntent.COMFORT)
    curr = _message(intent=MessageIntent.ENERGIZE)
    result = gate.evaluate(
        curr,
        _composition(intent=MessageIntent.ENERGIZE),
        previous_message=prev,
    )
    assert result.passed is False
    assert QualityCheck.CONSECUTIVE_COHERENCE in result.checks_failed


def test_consecutive_coherence_passes_accompany_then_comfort() -> None:
    """ACCOMPANY → COMFORT is a compatible emotional progression."""
    gate = QualityGate(checks=[QualityCheck.CONSECUTIVE_COHERENCE])
    prev = _message(intent=MessageIntent.ACCOMPANY)
    curr = _message(intent=MessageIntent.COMFORT)
    result = gate.evaluate(
        curr,
        _composition(intent=MessageIntent.COMFORT),
        previous_message=prev,
    )
    assert result.passed is True


def test_consecutive_coherence_passes_same_intent() -> None:
    """Same intent repeated is always coherent."""
    gate = QualityGate(checks=[QualityCheck.CONSECUTIVE_COHERENCE])
    prev = _message(intent=MessageIntent.AFFIRM)
    curr = _message(intent=MessageIntent.AFFIRM)
    result = gate.evaluate(
        curr,
        _composition(intent=MessageIntent.AFFIRM),
        previous_message=prev,
    )
    assert result.passed is True


def test_consecutive_coherence_passes_energize_then_affirm() -> None:
    """ENERGIZE → AFFIRM is a natural progression."""
    gate = QualityGate(checks=[QualityCheck.CONSECUTIVE_COHERENCE])
    prev = _message(intent=MessageIntent.ENERGIZE)
    curr = _message(intent=MessageIntent.AFFIRM)
    result = gate.evaluate(
        curr,
        _composition(intent=MessageIntent.AFFIRM),
        previous_message=prev,
    )
    assert result.passed is True


def test_consecutive_coherence_coherence_failure_reason_recorded() -> None:
    gate = QualityGate(checks=[QualityCheck.CONSECUTIVE_COHERENCE])
    prev = _message(intent=MessageIntent.COMFORT)
    curr = _message(intent=MessageIntent.ENERGIZE)
    result = gate.evaluate(
        curr,
        _composition(intent=MessageIntent.ENERGIZE),
        previous_message=prev,
    )
    assert any("comfort" in r.lower() or "energize" in r.lower() for r in result.failure_reasons)


def test_consecutive_coherence_no_previous_not_in_checks_failed() -> None:
    gate = QualityGate(checks=[QualityCheck.CONSECUTIVE_COHERENCE])
    result = gate.evaluate(
        _message(),
        _composition(),
        previous_message=None,
    )
    assert QualityCheck.CONSECUTIVE_COHERENCE not in result.checks_failed


# ---------------------------------------------------------------------------
# Full gate with all checks
# ---------------------------------------------------------------------------


def test_full_gate_clean_message_passes_all() -> None:
    gate = QualityGate(checks=_ALL_CHECKS)
    msg = _message("Morning! Miss you. 🐾", intent=MessageIntent.ACCOMPANY)
    comp = _composition(intent=MessageIntent.ACCOMPANY)
    result = gate.evaluate(msg, comp, previous_message=None)
    assert result.passed is True
    assert len(result.checks_run) == len(_ALL_CHECKS)
    assert result.checks_failed == []


# ---------------------------------------------------------------------------
# Opus review fix: TONE_MATCH must catch flat messages on high energy spec
# ---------------------------------------------------------------------------


def test_tone_match_fails_flat_message_with_high_energy_spec() -> None:
    """A flat, lifeless message contradicts a high energy spec (>0.7)."""
    high_energy = ToneSpectrum(
        warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
    )
    gate = QualityGate(checks=[QualityCheck.TONE_MATCH])
    # No exclamation, no caps, no emoji — flat and low-energy
    msg = _message("hey. i guess it is morning.", tone=high_energy)
    result = gate.evaluate(msg, _composition(tone=high_energy))
    assert result.passed is False
    assert QualityCheck.TONE_MATCH in result.checks_failed


def test_tone_match_passes_lively_message_with_high_energy_spec() -> None:
    """A lively message should pass the high energy spec check."""
    high_energy = ToneSpectrum(
        warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.9, vulnerability=0.3
    )
    gate = QualityGate(checks=[QualityCheck.TONE_MATCH])
    msg = _message("Good morning! Ready for a great day!", tone=high_energy)
    result = gate.evaluate(msg, _composition(tone=high_energy))
    assert result.passed is True

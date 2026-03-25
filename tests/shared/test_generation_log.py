"""Tests for MessageGenerationLog model and log_generation function."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.messaging.models import MessageIntent
from src.messaging.quality import QualityCheck, QualityResult
from src.personality.models import ToneSpectrum
from src.shared.generation_log import MessageGenerationLog, log_generation


UTC = timezone.utc


def _ts() -> datetime:
    return datetime(2026, 3, 24, 10, 0, tzinfo=UTC)


def _quality_result(passed: bool = True) -> QualityResult:
    return QualityResult(
        passed=passed,
        checks_run=[QualityCheck.LENGTH, QualityCheck.SAFETY],
        checks_failed=[] if passed else [QualityCheck.LENGTH],
        failure_reasons=[] if passed else ["Too long"],
    )


def _tone() -> ToneSpectrum:
    return ToneSpectrum(
        warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
    )


# ---------------------------------------------------------------------------
# MessageGenerationLog model validation
# ---------------------------------------------------------------------------


class TestMessageGenerationLog:
    def test_validates_with_all_required_fields(self) -> None:
        log = MessageGenerationLog(
            entity_id="e1",
            archetype_id="chaos_gremlin",
            composition_snapshot={"entity_id": "e1"},
            prompt_text="You are Jimi the dog.",
            prompt_tokens=150,
            generated_content="Woof! Miss you!",
            completion_tokens=12,
            model_used="claude-haiku-4-5",
            provider="anthropic",
            generation_latency_ms=320,
            cost_usd=0.000053,
            quality_gate_result={"passed": True},
            quality_gate_passed=True,
            regeneration_count=0,
            generated_at=_ts(),
        )
        assert log.entity_id == "e1"
        assert log.archetype_id == "chaos_gremlin"
        assert log.quality_gate_passed is True

    def test_effectiveness_fields_default_to_none(self) -> None:
        log = MessageGenerationLog(
            entity_id="e1",
            archetype_id="chaos_gremlin",
            composition_snapshot={},
            prompt_text="system prompt",
            prompt_tokens=100,
            generated_content="Hey!",
            completion_tokens=5,
            model_used="claude-haiku-4-5",
            provider="anthropic",
            generation_latency_ms=200,
            cost_usd=0.00003,
            quality_gate_result={},
            quality_gate_passed=True,
            regeneration_count=0,
            generated_at=_ts(),
        )
        assert log.effectiveness_score is None
        assert log.user_reaction is None
        assert log.user_replied is None
        assert log.reply_sentiment is None

    def test_recipient_id_defaults_to_none(self) -> None:
        log = MessageGenerationLog(
            entity_id="e1",
            archetype_id="chaos_gremlin",
            composition_snapshot={},
            prompt_text="system prompt",
            prompt_tokens=100,
            generated_content="Hey!",
            completion_tokens=5,
            model_used="claude-haiku-4-5",
            provider="anthropic",
            generation_latency_ms=200,
            cost_usd=0.00003,
            quality_gate_result={},
            quality_gate_passed=True,
            regeneration_count=0,
            generated_at=_ts(),
        )
        assert log.recipient_id is None

    def test_rejects_missing_required_fields(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MessageGenerationLog(entity_id="e1")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# log_generation function
# ---------------------------------------------------------------------------


class TestLogGeneration:
    def _make_inputs(self) -> tuple:
        """Return (composition, generated_message, quality_result, prompt_text)."""
        from datetime import datetime, timezone
        from unittest.mock import MagicMock

        from src.messaging.generator import GeneratedMessage
        from src.messaging.intent import IntentProfile, TrustStage
        from src.messaging.recipient import RecipientState
        from src.messaging.signals import (
            ContextSignal,
            ContextSignalBundle,
            ContextSignalSource,
        )
        from src.messaging.composer import MessageComposition
        from src.personality.enums import EnergyLevel
        from src.personality.models import (
            CommunicationStyle,
            EmotionalDisposition,
            EntityProfile,
            KnowledgeAwareness,
            RelationalStance,
        )

        ts = datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc)

        entity = EntityProfile(
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
                domain_knowledge=["daily routines"],
                user_context_fields=["name"],
                temporal_awareness=True,
                memory_references=True,
            ),
            primary_archetype="chaos_gremlin",
            archetype_weights={i.value: 1.0 / 14 for i in MessageIntent},
            forbidden_phrases=[],
            forbidden_topics=[],
        )

        composition = MessageComposition(
            entity_voice=entity,
            intent=IntentProfile(primary_intent=MessageIntent.ENERGIZE, intensity=0.7),
            tone=_tone(),
            tone_adjustments_applied=[],
            signals=ContextSignalBundle(
                signals=[
                    ContextSignal(
                        source=ContextSignalSource.TIME,
                        signal_key="time_of_day",
                        signal_value="morning",
                        timestamp=ts,
                    )
                ],
                user_id="u1",
                entity_id="e1",
                generated_at=ts,
            ),
            recipient_state=RecipientState(
                likely_availability="busy",
                likely_energy=0.55,
                likely_receptivity=0.35,
                emotional_context="neutral",
                state_confidence=0.33,
            ),
            trust_stage=TrustStage.WORKING,
            relationship_depth=10,
            recent_messages=[],
            last_user_reply=None,
            message_category="greeting",
            max_characters=160,
            channel="sms",
        )

        generated = GeneratedMessage(
            message_id="m1",
            entity_id="e1",
            content="Woof! Miss you!",
            generated_at=ts,
            model_used="claude-haiku-4-5",
            prompt_tokens=150,
            completion_tokens=12,
            message_category="greeting",
            intended_intent=MessageIntent.ENERGIZE,
            intended_tone=_tone(),
            character_count=15,
            provider="anthropic",
            cost_usd=0.000053,
            latency_ms=320,
        )

        quality = _quality_result(passed=True)
        prompt_text = "You are Sparky the dog."

        return composition, generated, quality, prompt_text

    def test_returns_message_generation_log(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert isinstance(result, MessageGenerationLog)

    def test_content_matches_generated_message(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert result.generated_content == generated.content

    def test_entity_id_from_composition(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert result.entity_id == "e1"

    def test_archetype_id_from_entity_profile(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert result.archetype_id == "chaos_gremlin"

    def test_quality_gate_passed_from_result(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert result.quality_gate_passed is True

    def test_prompt_text_stored(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert result.prompt_text == prompt_text

    def test_composition_snapshot_is_dict(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert isinstance(result.composition_snapshot, dict)

    def test_effectiveness_fields_are_none(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert result.effectiveness_score is None
        assert result.user_reaction is None
        assert result.user_replied is None

    def test_log_stored_locally(self) -> None:
        """log_generation appends to in-memory store; store is non-empty after call."""
        from src.shared.generation_log import get_log_store

        composition, generated, quality, prompt_text = self._make_inputs()
        log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert len(get_log_store()) > 0

    def test_recipient_id_falls_back_to_composition(self) -> None:
        """When no explicit recipient_id is passed, use composition.recipient_id."""
        composition, generated, quality, prompt_text = self._make_inputs()
        composition.recipient_id = "owner-u1"
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
        )
        assert result.recipient_id == "owner-u1"

    def test_explicit_recipient_id_overrides_composition(self) -> None:
        composition, generated, quality, prompt_text = self._make_inputs()
        composition.recipient_id = "owner-u1"
        result = log_generation(
            composition=composition,
            generated=generated,
            quality=quality,
            prompt_text=prompt_text,
            recipient_id="explicit-r1",
        )
        assert result.recipient_id == "explicit-r1"

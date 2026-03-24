"""Tests for generation logging wired into generate_message (Task 7)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.messaging.composer import MessageComposition
from src.messaging.intent import IntentProfile, TrustStage
from src.messaging.models import MessageIntent
from src.messaging.recipient import RecipientState
from src.messaging.signals import ContextSignal, ContextSignalBundle, ContextSignalSource
from src.personality.enums import EnergyLevel
from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    EntityProfile,
    KnowledgeAwareness,
    RelationalStance,
    ToneSpectrum,
)
from src.messaging.generator import generate_message
from src.shared.llm import (
    AnthropicProvider,
    LLMProvider,
    LLMResponse,
    ModelConfig,
    RoutingDecision,
)

UTC = timezone.utc


def _ts() -> datetime:
    return datetime(2026, 3, 24, 10, 0, tzinfo=UTC)


def _entity() -> EntityProfile:
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


def _composition() -> MessageComposition:
    return MessageComposition(
        entity_voice=_entity(),
        intent=IntentProfile(primary_intent=MessageIntent.ENERGIZE, intensity=0.7),
        tone=ToneSpectrum(
            warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
        ),
        tone_adjustments_applied=[],
        signals=ContextSignalBundle(
            signals=[
                ContextSignal(
                    source=ContextSignalSource.TIME,
                    signal_key="time_of_day",
                    signal_value="morning",
                    timestamp=_ts(),
                )
            ],
            user_id="u1",
            entity_id="e1",
            generated_at=_ts(),
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


def _mock_provider(text: str = "Woof! Hey! 🐾") -> AnthropicProvider:
    routing = RoutingDecision(
        selected_model=ModelConfig(
            provider=LLMProvider.ANTHROPIC,
            model_id="claude-haiku-4-5",
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            max_tokens=200,
        ),
        reason="primary",
        fallback_chain=[],
        routing_rule="default",
    )
    provider = MagicMock(spec=AnthropicProvider)
    provider.generate = AsyncMock(
        return_value=LLMResponse(
            content=text,
            provider=LLMProvider.ANTHROPIC,
            model_id="claude-haiku-4-5",
            input_tokens=150,
            output_tokens=12,
            cost_usd=0.000053,
            latency_ms=320,
            routing_decision=routing,
        )
    )
    return provider


# ---------------------------------------------------------------------------
# Generation still works with logging present
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generation_succeeds_with_logging() -> None:
    result = await generate_message(_composition(), provider=_mock_provider())
    assert result.content == "Woof! Hey! 🐾"


@pytest.mark.asyncio
async def test_generation_result_unaffected_by_logging() -> None:
    """The return value is the GeneratedMessage, not the log record."""
    from src.messaging.generator import GeneratedMessage

    result = await generate_message(_composition(), provider=_mock_provider())
    assert isinstance(result, GeneratedMessage)


@pytest.mark.asyncio
async def test_log_created_after_generation() -> None:
    """After a successful generation, log_generation is called."""
    with patch("src.messaging.generator.log_generation") as mock_log:
        await generate_message(_composition(), provider=_mock_provider())
    mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_log_receives_correct_composition() -> None:
    comp = _composition()
    with patch("src.messaging.generator.log_generation") as mock_log:
        await generate_message(comp, provider=_mock_provider())
    call_kwargs = mock_log.call_args.kwargs
    assert call_kwargs["composition"] is comp


@pytest.mark.asyncio
async def test_log_receives_prompt_text() -> None:
    with patch("src.messaging.generator.log_generation") as mock_log:
        await generate_message(_composition(), provider=_mock_provider())
    call_kwargs = mock_log.call_args.kwargs
    assert isinstance(call_kwargs["prompt_text"], str)
    assert len(call_kwargs["prompt_text"]) > 0


@pytest.mark.asyncio
async def test_log_receives_quality_result() -> None:
    with patch("src.messaging.generator.log_generation") as mock_log:
        await generate_message(_composition(), provider=_mock_provider())
    call_kwargs = mock_log.call_args.kwargs
    from src.messaging.quality import QualityResult
    assert isinstance(call_kwargs["quality"], QualityResult)


# ---------------------------------------------------------------------------
# Graceful degradation — logging failure must not break generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generation_succeeds_when_logging_fails() -> None:
    """A logging error must NOT propagate — generation must still return."""
    with patch(
        "src.messaging.generator.log_generation", side_effect=Exception("DB down")
    ):
        result = await generate_message(_composition(), provider=_mock_provider())

    assert result.content == "Woof! Hey! 🐾"


@pytest.mark.asyncio
async def test_generation_result_correct_when_logging_fails() -> None:
    from src.messaging.generator import GeneratedMessage

    with patch(
        "src.messaging.generator.log_generation", side_effect=RuntimeError("storage full")
    ):
        result = await generate_message(_composition(), provider=_mock_provider())

    assert isinstance(result, GeneratedMessage)
    assert result.entity_id == "e1"

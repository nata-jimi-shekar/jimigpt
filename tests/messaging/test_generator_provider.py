"""Tests for generate_message using the BaseProvider abstraction (Task 3)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

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
from src.messaging.generator import GeneratedMessage, generate_message
from src.shared.llm import (
    AnthropicProvider,
    BaseProvider,
    LLMProvider,
    LLMResponse,
    ModelConfig,
    RoutingDecision,
)

UTC = timezone.utc


def _ts() -> datetime:
    return datetime(2026, 3, 23, 10, 0, tzinfo=UTC)


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
        forbidden_phrases=["I'm just an AI"],
        forbidden_topics=[],
    )


def _composition() -> MessageComposition:
    e = _entity()
    return MessageComposition(
        entity_voice=e,
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


def _make_routing_decision() -> RoutingDecision:
    return RoutingDecision(
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


def _mock_llm_response(text: str = "Hey! 🐾") -> LLMResponse:
    return LLMResponse(
        content=text,
        provider=LLMProvider.ANTHROPIC,
        model_id="claude-haiku-4-5",
        input_tokens=150,
        output_tokens=12,
        cost_usd=0.000053,
        latency_ms=320,
        routing_decision=_make_routing_decision(),
    )


def _mock_provider(text: str = "Hey! 🐾") -> BaseProvider:
    """Mock BaseProvider that returns a fixed LLMResponse."""
    provider = MagicMock(spec=AnthropicProvider)
    provider.generate = AsyncMock(return_value=_mock_llm_response(text))
    return provider


# ---------------------------------------------------------------------------
# generate_message via BaseProvider
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_message_with_provider_returns_generated_message() -> None:
    result = await generate_message(_composition(), provider=_mock_provider())
    assert isinstance(result, GeneratedMessage)


@pytest.mark.asyncio
async def test_generate_message_with_provider_content_populated() -> None:
    result = await generate_message(_composition(), provider=_mock_provider("Woof!"))
    assert result.content == "Woof!"


@pytest.mark.asyncio
async def test_generate_message_with_provider_maps_token_counts() -> None:
    result = await generate_message(_composition(), provider=_mock_provider())
    assert result.prompt_tokens == 150
    assert result.completion_tokens == 12


@pytest.mark.asyncio
async def test_generate_message_with_provider_records_cost() -> None:
    result = await generate_message(_composition(), provider=_mock_provider())
    assert result.cost_usd >= 0.0


@pytest.mark.asyncio
async def test_generate_message_with_provider_records_latency() -> None:
    result = await generate_message(_composition(), provider=_mock_provider())
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_generate_message_with_provider_records_provider_name() -> None:
    result = await generate_message(_composition(), provider=_mock_provider())
    assert result.provider == "anthropic"


@pytest.mark.asyncio
async def test_generate_message_provider_generate_called_once() -> None:
    mock = _mock_provider()
    await generate_message(_composition(), provider=mock)
    mock.generate.assert_called_once()


# ---------------------------------------------------------------------------
# GeneratedMessage new fields have safe defaults (existing tests unaffected)
# ---------------------------------------------------------------------------


def test_generated_message_provider_defaults_to_anthropic() -> None:
    msg = GeneratedMessage(
        message_id="m1",
        entity_id="e1",
        content="hi",
        generated_at=_ts(),
        model_used="claude-sonnet-4-6",
        prompt_tokens=10,
        completion_tokens=2,
        message_category="greeting",
        intended_intent=MessageIntent.ENERGIZE,
        intended_tone=ToneSpectrum(
            warmth=0.5, humor=0.5, directness=0.5, gravity=0.5, energy=0.5, vulnerability=0.5
        ),
        character_count=2,
    )
    assert msg.provider == "anthropic"
    assert msg.cost_usd == 0.0
    assert msg.latency_ms == 0

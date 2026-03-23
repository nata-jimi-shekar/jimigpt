"""Tests for the LLM message generator (Anthropic API mocked)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.messaging.composer import MessageComposition, MessageComposer
from src.messaging.intent import IntentProfile, TrustStage
from src.messaging.models import MessageIntent
from src.messaging.recipient import RecipientState, TrustProfile
from src.messaging.signals import ContextSignal, ContextSignalBundle, ContextSignalSource
from src.messaging.tone import ToneRule
from src.messaging.triggers import TriggerRule, TriggerType
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

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ts() -> datetime:
    return datetime(2026, 3, 23, 10, 0, tzinfo=UTC)


def _entity(name: str = "Sparky") -> EntityProfile:
    return EntityProfile(
        entity_id="e1",
        entity_name=name,
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
        forbidden_phrases=["I'm just an AI", "as an AI"],
        forbidden_topics=[],
    )


def _composition(entity: EntityProfile | None = None, message_category: str = "greeting") -> MessageComposition:
    e = entity or _entity()
    return MessageComposition(
        entity_voice=e,
        intent=IntentProfile(primary_intent=MessageIntent.ENERGIZE, intensity=0.7),
        tone=ToneSpectrum(warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3),
        tone_adjustments_applied=[],
        signals=ContextSignalBundle(
            signals=[
                ContextSignal(
                    source=ContextSignalSource.TIME,
                    signal_key="time_of_day",
                    signal_value="morning",
                    timestamp=_ts(),
                ),
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
        message_category=message_category,
        max_characters=160,
        channel="sms",
    )


def _mock_client(content: str = "Hey! Good morning! 🐾") -> MagicMock:
    """Build a mock AsyncAnthropic client returning a fixed message."""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=content)]
    mock_response.usage.input_tokens = 150
    mock_response.usage.output_tokens = 12
    client.messages.create = AsyncMock(return_value=mock_response)
    return client


# ---------------------------------------------------------------------------
# GeneratedMessage model
# ---------------------------------------------------------------------------


def test_generated_message_constructs() -> None:
    msg = GeneratedMessage(
        message_id="m1",
        entity_id="e1",
        content="Good morning!",
        generated_at=_ts(),
        model_used="claude-sonnet-4-6",
        prompt_tokens=120,
        completion_tokens=8,
        message_category="greeting",
        intended_intent=MessageIntent.ENERGIZE,
        intended_tone=ToneSpectrum(
            warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
        ),
        character_count=13,
    )
    assert msg.content == "Good morning!"
    assert msg.intended_intent == MessageIntent.ENERGIZE
    assert msg.character_count == 13


def test_generated_message_character_count_must_be_non_negative() -> None:
    with pytest.raises(Exception):
        GeneratedMessage(
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
            character_count=-1,
        )


def test_generated_message_token_counts_non_negative() -> None:
    with pytest.raises(Exception):
        GeneratedMessage(
            message_id="m1",
            entity_id="e1",
            content="hi",
            generated_at=_ts(),
            model_used="claude-sonnet-4-6",
            prompt_tokens=-1,
            completion_tokens=2,
            message_category="greeting",
            intended_intent=MessageIntent.ENERGIZE,
            intended_tone=ToneSpectrum(
                warmth=0.5, humor=0.5, directness=0.5, gravity=0.5, energy=0.5, vulnerability=0.5
            ),
            character_count=2,
        )


# ---------------------------------------------------------------------------
# generate_message — structure and return type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_message_returns_generated_message() -> None:
    result = await generate_message(_composition(), client=_mock_client())
    assert isinstance(result, GeneratedMessage)


@pytest.mark.asyncio
async def test_generate_message_content_non_empty() -> None:
    result = await generate_message(_composition(), client=_mock_client("Morning vibes! 🌟"))
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_generate_message_content_matches_api_response() -> None:
    result = await generate_message(_composition(), client=_mock_client("Hey there! 🐾"))
    assert result.content == "Hey there! 🐾"


@pytest.mark.asyncio
async def test_generate_message_entity_id_from_composition() -> None:
    result = await generate_message(_composition(_entity()), client=_mock_client())
    assert result.entity_id == "e1"


@pytest.mark.asyncio
async def test_generate_message_category_from_composition() -> None:
    result = await generate_message(_composition(message_category="caring"), client=_mock_client())
    assert result.message_category == "caring"


@pytest.mark.asyncio
async def test_generate_message_intended_intent_from_composition() -> None:
    comp = _composition()
    result = await generate_message(comp, client=_mock_client())
    assert result.intended_intent == comp.intent.primary_intent


@pytest.mark.asyncio
async def test_generate_message_intended_tone_from_composition() -> None:
    comp = _composition()
    result = await generate_message(comp, client=_mock_client())
    assert result.intended_tone == comp.tone


@pytest.mark.asyncio
async def test_generate_message_character_count_matches_content() -> None:
    content = "Rise and shine! 🌞"
    result = await generate_message(_composition(), client=_mock_client(content))
    assert result.character_count == len(content)


@pytest.mark.asyncio
async def test_generate_message_model_used_recorded() -> None:
    result = await generate_message(
        _composition(), model="claude-sonnet-4-6", client=_mock_client()
    )
    assert result.model_used == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_generate_message_prompt_tokens_from_api() -> None:
    result = await generate_message(_composition(), client=_mock_client())
    assert result.prompt_tokens == 150


@pytest.mark.asyncio
async def test_generate_message_completion_tokens_from_api() -> None:
    result = await generate_message(_composition(), client=_mock_client())
    assert result.completion_tokens == 12


@pytest.mark.asyncio
async def test_generate_message_generated_at_is_set() -> None:
    result = await generate_message(_composition(), client=_mock_client())
    assert result.generated_at is not None
    assert result.generated_at.tzinfo is not None


@pytest.mark.asyncio
async def test_generate_message_message_id_is_unique() -> None:
    client = _mock_client()
    comp = _composition()
    r1 = await generate_message(comp, client=client)
    r2 = await generate_message(comp, client=client)
    assert r1.message_id != r2.message_id


# ---------------------------------------------------------------------------
# generate_message — API call behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_message_calls_api_once() -> None:
    client = _mock_client()
    await generate_message(_composition(), client=client)
    client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_message_passes_model_to_api() -> None:
    client = _mock_client()
    await generate_message(_composition(), model="claude-sonnet-4-6", client=client)
    call_kwargs = client.messages.create.call_args
    assert call_kwargs.kwargs.get("model") == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_generate_message_passes_max_tokens_to_api() -> None:
    client = _mock_client()
    await generate_message(_composition(), max_tokens=300, client=client)
    call_kwargs = client.messages.create.call_args
    assert call_kwargs.kwargs.get("max_tokens") == 300


@pytest.mark.asyncio
async def test_generate_message_system_prompt_sent_to_api() -> None:
    """The composed system prompt is passed as the system parameter."""
    client = _mock_client()
    await generate_message(_composition(), client=client)
    call_kwargs = client.messages.create.call_args
    system = call_kwargs.kwargs.get("system", "")
    assert len(system) > 0


@pytest.mark.asyncio
async def test_generate_message_user_message_in_api_call() -> None:
    """A user-role message is included to trigger generation."""
    client = _mock_client()
    await generate_message(_composition(), client=client)
    call_kwargs = client.messages.create.call_args
    messages = call_kwargs.kwargs.get("messages", [])
    assert any(m.get("role") == "user" for m in messages)


# ---------------------------------------------------------------------------
# Property-based: content characteristics (via mock)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generated_content_under_160_chars() -> None:
    """SMS constraint: content must be under 160 characters."""
    short_content = "Good morning! 🌞"
    result = await generate_message(_composition(), client=_mock_client(short_content))
    assert result.character_count <= 160


@pytest.mark.asyncio
async def test_generated_content_no_forbidden_phrases() -> None:
    """Forbidden phrases must not appear in generated content."""
    entity = _entity()
    clean_content = "Rise and shine, the day is yours!"
    result = await generate_message(_composition(entity), client=_mock_client(clean_content))
    for phrase in entity.forbidden_phrases:
        assert phrase.lower() not in result.content.lower()


# ---------------------------------------------------------------------------
# Default model constant
# ---------------------------------------------------------------------------


def test_default_model_is_claude_sonnet() -> None:
    from src.messaging.generator import DEFAULT_MODEL
    assert "claude" in DEFAULT_MODEL
    assert "sonnet" in DEFAULT_MODEL

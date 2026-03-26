"""Tests for the personality-to-prompt translator."""

import pytest

from src.personality.enums import EnergyLevel
from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    EntityProfile,
    KnowledgeAwareness,
    RelationalStance,
)
from src.personality.prompt_builder import (
    AssembledPrompt,
    MessageContext,
    PromptBlock,
    assemble_prompt,
)

EXPECTED_LAYERS = {
    "identity",
    "communication",
    "emotional",
    "relational",
    "knowledge",
    "trust_relationship",
    "anti_patterns",
    "message_directive",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_profile() -> EntityProfile:
    return EntityProfile(
        entity_id="test-entity-001",
        entity_name="Biscuit",
        entity_type="pet",
        product="jimigpt",
        communication=CommunicationStyle(
            sentence_length="short",
            energy_level=EnergyLevel.HIGH,
            emoji_usage="heavy",
            punctuation_style="excited_exclamations",
            vocabulary_level="simple",
            quirks=["uses ALL CAPS for excitement"],
        ),
        emotional=EmotionalDisposition(
            baseline_mood="playful",
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
            domain_knowledge=["food and treats", "toys and play"],
            user_context_fields=["owner_schedule", "feeding_times"],
            temporal_awareness=True,
            memory_references=True,
        ),
        primary_archetype="jimigpt:chaos_gremlin",
        forbidden_phrases=["As an AI", "I understand how you feel"],
        forbidden_topics=["veterinary advice"],
    )


@pytest.fixture
def sample_context() -> MessageContext:
    return MessageContext(
        message_category="greeting",
        max_characters=160,
        channel="sms",
    )


# ---------------------------------------------------------------------------
# Return type and structure
# ---------------------------------------------------------------------------


def test_assemble_prompt_returns_assembled_prompt(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    assert isinstance(result, AssembledPrompt)


def test_assemble_prompt_system_prompt_not_empty(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    assert result.system_prompt.strip() != ""


def test_assemble_prompt_has_8_blocks(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    assert result.block_count == 8
    assert len(result.blocks) == 8


def test_assemble_prompt_block_count_matches_blocks_list(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    assert result.block_count == len(result.blocks)


def test_assemble_prompt_all_layers_present(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    layers = {block.layer for block in result.blocks}
    assert layers == EXPECTED_LAYERS


def test_assemble_prompt_blocks_ordered_by_priority(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    priorities = [block.priority for block in result.blocks]
    assert priorities == sorted(priorities)


def test_assemble_prompt_entity_profile_id(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    assert result.entity_profile_id == sample_profile.entity_id


# ---------------------------------------------------------------------------
# Content correctness
# ---------------------------------------------------------------------------


def test_assemble_prompt_entity_name_in_system_prompt(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    assert "Biscuit" in result.system_prompt


def test_assemble_prompt_forbidden_phrase_in_anti_patterns_block(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    anti_block = next(b for b in result.blocks if b.layer == "anti_patterns")
    assert "As an AI" in anti_block.content


def test_assemble_prompt_forbidden_topic_in_anti_patterns_block(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    anti_block = next(b for b in result.blocks if b.layer == "anti_patterns")
    assert "veterinary advice" in anti_block.content


def test_assemble_prompt_message_category_in_directive_block(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    directive = next(b for b in result.blocks if b.layer == "message_directive")
    assert "greeting" in directive.content


def test_assemble_prompt_no_template_artifacts(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result = assemble_prompt(sample_profile, sample_context)
    assert "{{" not in result.system_prompt
    assert "}}" not in result.system_prompt


# ---------------------------------------------------------------------------
# Snapshot: determinism
# ---------------------------------------------------------------------------


def test_assemble_prompt_same_profile_same_output(
    sample_profile: EntityProfile, sample_context: MessageContext
) -> None:
    result_a = assemble_prompt(sample_profile, sample_context)
    result_b = assemble_prompt(sample_profile, sample_context)
    assert result_a.system_prompt == result_b.system_prompt
    assert result_a.block_count == result_b.block_count


# ---------------------------------------------------------------------------
# MessageContext — typed input validation (Critical Fix #2)
# ---------------------------------------------------------------------------


def test_message_context_defaults() -> None:
    ctx = MessageContext(message_category="morning")
    assert ctx.max_characters == 160
    assert ctx.channel is None


def test_message_context_max_characters_must_be_positive() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        MessageContext(message_category="greeting", max_characters=0)


def test_message_context_fields_surface_in_directive(
    sample_profile: EntityProfile,
) -> None:
    ctx = MessageContext(message_category="morning_checkin", max_characters=280, channel="sms")
    result = assemble_prompt(sample_profile, ctx)
    directive = next(b for b in result.blocks if b.layer == "message_directive")
    assert "morning_checkin" in directive.content

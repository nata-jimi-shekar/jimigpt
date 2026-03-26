"""Tests for trust-stage integration with message prompt generation.

Core requirement: same entity at different trust stages produces different
prompts from assemble_prompt().

Covers:
- MessageContext accepts trust_stage field
- trust_stage defaults to STRANGER (safe Phase 1 default)
- Trust stage name appears in the assembled system prompt
- Different trust stages produce different prompt content
- Trust-aware instructions differ across stages (stranger/working/deep)
- Existing prompts (no trust_stage set) continue to work unchanged
"""

import pytest

from src.personality.enums import EnergyLevel
from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    EntityProfile,
    KnowledgeAwareness,
    RelationalStance,
)
from src.personality.prompt_builder import MessageContext, assemble_prompt
from src.trust.ladder import TrustStage

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def entity() -> EntityProfile:
    return EntityProfile(
        entity_id="e-001",
        entity_name="Mochi",
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
            domain_knowledge=["treats", "naps"],
            user_context_fields=["schedule"],
            temporal_awareness=True,
            memory_references=True,
        ),
        primary_archetype="jimigpt:chaos_gremlin",
        forbidden_phrases=["As an AI"],
        forbidden_topics=["veterinary advice"],
    )


# ---------------------------------------------------------------------------
# MessageContext — trust_stage field
# ---------------------------------------------------------------------------


def test_message_context_accepts_trust_stage() -> None:
    """MessageContext accepts trust_stage as a field."""
    ctx = MessageContext(
        message_category="greeting",
        trust_stage=TrustStage.WORKING,
    )
    assert ctx.trust_stage == TrustStage.WORKING


def test_message_context_trust_stage_defaults_to_stranger() -> None:
    """trust_stage defaults to STRANGER — safe baseline for new relationships."""
    ctx = MessageContext(message_category="greeting")
    assert ctx.trust_stage == TrustStage.STRANGER


def test_message_context_accepts_all_trust_stages() -> None:
    """All TrustStage values are valid on MessageContext."""
    for stage in TrustStage:
        ctx = MessageContext(message_category="greeting", trust_stage=stage)
        assert ctx.trust_stage == stage


# ---------------------------------------------------------------------------
# Trust stage appears in assembled prompt
# ---------------------------------------------------------------------------


def test_trust_stage_name_in_prompt_stranger(entity: EntityProfile) -> None:
    """STRANGER trust stage name appears in the system prompt."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.STRANGER)
    result = assemble_prompt(entity, ctx)
    assert "stranger" in result.system_prompt.lower()


def test_trust_stage_name_in_prompt_working(entity: EntityProfile) -> None:
    """WORKING trust stage name appears in the system prompt."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.WORKING)
    result = assemble_prompt(entity, ctx)
    assert "working" in result.system_prompt.lower()


def test_trust_stage_name_in_prompt_deep(entity: EntityProfile) -> None:
    """DEEP trust stage name appears in the system prompt."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.DEEP)
    result = assemble_prompt(entity, ctx)
    assert "deep" in result.system_prompt.lower()


# ---------------------------------------------------------------------------
# Core requirement: different trust stages → different prompts
# ---------------------------------------------------------------------------


def test_stranger_and_working_produce_different_prompts(entity: EntityProfile) -> None:
    """Same entity at STRANGER vs WORKING produces different system prompts."""
    stranger_ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.STRANGER)
    working_ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.WORKING)

    stranger_prompt = assemble_prompt(entity, stranger_ctx)
    working_prompt = assemble_prompt(entity, working_ctx)

    assert stranger_prompt.system_prompt != working_prompt.system_prompt


def test_working_and_deep_produce_different_prompts(entity: EntityProfile) -> None:
    """Same entity at WORKING vs DEEP produces different system prompts."""
    working_ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.WORKING)
    deep_ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.DEEP)

    working_prompt = assemble_prompt(entity, working_ctx)
    deep_prompt = assemble_prompt(entity, deep_ctx)

    assert working_prompt.system_prompt != deep_prompt.system_prompt


def test_all_five_trust_stages_produce_distinct_prompts(entity: EntityProfile) -> None:
    """All five trust stages produce distinct prompt content."""
    prompts = [
        assemble_prompt(
            entity,
            MessageContext(message_category="greeting", trust_stage=stage),
        ).system_prompt
        for stage in TrustStage
    ]
    # All 5 prompts are unique
    assert len(set(prompts)) == 5


# ---------------------------------------------------------------------------
# Trust block exists as a named block in the assembled prompt
# ---------------------------------------------------------------------------


def test_trust_relationship_block_present(entity: EntityProfile) -> None:
    """Assembled prompt includes a 'trust_relationship' block."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.WORKING)
    result = assemble_prompt(entity, ctx)
    layers = {block.layer for block in result.blocks}
    assert "trust_relationship" in layers


def test_trust_block_contains_stage_name(entity: EntityProfile) -> None:
    """The trust_relationship block contains the current stage name."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.ALLIANCE)
    result = assemble_prompt(entity, ctx)
    trust_block = next(b for b in result.blocks if b.layer == "trust_relationship")
    assert "alliance" in trust_block.content.lower()


# ---------------------------------------------------------------------------
# Stage-specific instructions
# ---------------------------------------------------------------------------


def test_stranger_instructions_mention_low_pressure(entity: EntityProfile) -> None:
    """STRANGER stage instructions guide toward gentle, low-pressure messages."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.STRANGER)
    result = assemble_prompt(entity, ctx)
    trust_block = next(b for b in result.blocks if b.layer == "trust_relationship")
    # The instructions should convey low-pressure / introductory tone
    assert any(
        word in trust_block.content.lower()
        for word in ("low-pressure", "low pressure", "light", "gentle", "getting to know")
    )


def test_working_instructions_mention_past_or_history(entity: EntityProfile) -> None:
    """WORKING stage instructions reference past interactions."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.WORKING)
    result = assemble_prompt(entity, ctx)
    trust_block = next(b for b in result.blocks if b.layer == "trust_relationship")
    assert any(
        word in trust_block.content.lower()
        for word in ("past", "reference", "naturally", "know each other")
    )


def test_deep_instructions_mention_patterns_or_bond(entity: EntityProfile) -> None:
    """DEEP stage instructions guide toward reflecting deep bond/patterns."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.DEEP)
    result = assemble_prompt(entity, ctx)
    trust_block = next(b for b in result.blocks if b.layer == "trust_relationship")
    assert any(
        word in trust_block.content.lower()
        for word in ("pattern", "bond", "deep", "reflect")
    )


# ---------------------------------------------------------------------------
# Backwards compatibility — existing context without trust_stage still works
# ---------------------------------------------------------------------------


def test_prompt_assembles_without_explicit_trust_stage(entity: EntityProfile) -> None:
    """MessageContext without trust_stage still produces a valid prompt."""
    ctx = MessageContext(message_category="greeting")
    result = assemble_prompt(entity, ctx)
    assert result.system_prompt.strip() != ""
    assert result.block_count == 8


def test_no_template_artifacts_with_trust_stage(entity: EntityProfile) -> None:
    """No unrendered Jinja2 tags in the output when trust_stage is set."""
    ctx = MessageContext(message_category="greeting", trust_stage=TrustStage.DEEP)
    result = assemble_prompt(entity, ctx)
    assert "{{" not in result.system_prompt
    assert "}}" not in result.system_prompt

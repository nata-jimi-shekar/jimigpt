"""Tests for four-layer personality Pydantic models."""

import pytest
from pydantic import ValidationError

from src.personality.enums import EnergyLevel
from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    EntityProfile,
    KnowledgeAwareness,
    RelationalStance,
)

# ---------------------------------------------------------------------------
# CommunicationStyle
# ---------------------------------------------------------------------------


def test_communication_style_valid(sample_communication_style: dict) -> None:
    style = CommunicationStyle(**sample_communication_style)
    assert style.sentence_length == "short"
    assert style.energy_level == EnergyLevel.HIGH
    assert style.emoji_usage == "heavy"
    assert style.punctuation_style == "excited_exclamations"
    assert style.vocabulary_level == "simple"
    assert style.quirks == ["uses ALL CAPS for excitement"]


def test_communication_style_quirks_defaults_to_empty() -> None:
    style = CommunicationStyle(
        sentence_length="medium",
        energy_level="low",
        emoji_usage="none",
        punctuation_style="calm_periods",
        vocabulary_level="moderate",
    )
    assert style.quirks == []


def test_communication_style_invalid_energy_level() -> None:
    with pytest.raises(ValidationError):
        CommunicationStyle(
            sentence_length="short",
            energy_level="extreme",  # not a valid EnergyLevel
            emoji_usage="none",
            punctuation_style="calm_periods",
            vocabulary_level="simple",
        )


def test_communication_style_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        CommunicationStyle(
            energy_level="high",
            emoji_usage="none",
            punctuation_style="calm_periods",
            vocabulary_level="simple",
            # sentence_length missing
        )


# ---------------------------------------------------------------------------
# EmotionalDisposition
# ---------------------------------------------------------------------------


def test_emotional_disposition_valid(sample_emotional_disposition: dict) -> None:
    disposition = EmotionalDisposition(**sample_emotional_disposition)
    assert disposition.baseline_mood == "playful"
    assert disposition.emotional_range == "wide"
    assert disposition.need_expression == "dramatic"
    assert disposition.humor_style == "silly"


def test_emotional_disposition_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        EmotionalDisposition(
            baseline_mood="calm",
            emotional_range="narrow",
            # need_expression missing
            humor_style="none",
        )


# ---------------------------------------------------------------------------
# RelationalStance
# ---------------------------------------------------------------------------


def test_relational_stance_valid(sample_relational_stance: dict) -> None:
    stance = RelationalStance(**sample_relational_stance)
    assert stance.attachment_style == "clingy"
    assert stance.initiative_style == "proactive"
    assert stance.boundary_respect == "moderate"
    assert stance.warmth_level == "intense"


def test_relational_stance_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        RelationalStance(
            attachment_style="balanced",
            initiative_style="responsive",
            # boundary_respect missing
            warmth_level="warm",
        )


# ---------------------------------------------------------------------------
# KnowledgeAwareness
# ---------------------------------------------------------------------------


def test_knowledge_awareness_valid(sample_knowledge_awareness: dict) -> None:
    knowledge = KnowledgeAwareness(**sample_knowledge_awareness)
    assert knowledge.domain_knowledge == ["food and treats", "toys and play"]
    assert knowledge.user_context_fields == ["owner_schedule", "feeding_times"]
    assert knowledge.temporal_awareness is True
    assert knowledge.memory_references is True


def test_knowledge_awareness_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        KnowledgeAwareness(
            # domain_knowledge missing
            user_context_fields=["owner_schedule"],
            temporal_awareness=True,
            memory_references=False,
        )


# ---------------------------------------------------------------------------
# EntityProfile — composes all four layers
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_entity_profile(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> EntityProfile:
    return EntityProfile(
        entity_id="ent-001",
        entity_name="Biscuit",
        entity_type="pet",
        product="jimigpt",
        communication=sample_communication_style,
        emotional=sample_emotional_disposition,
        relational=sample_relational_stance,
        knowledge=sample_knowledge_awareness,
        primary_archetype="chaos_gremlin",
    )


def test_entity_profile_composes_all_four_layers(
    sample_entity_profile: EntityProfile,
) -> None:
    assert isinstance(sample_entity_profile.communication, CommunicationStyle)
    assert isinstance(sample_entity_profile.emotional, EmotionalDisposition)
    assert isinstance(sample_entity_profile.relational, RelationalStance)
    assert isinstance(sample_entity_profile.knowledge, KnowledgeAwareness)


def test_entity_profile_core_fields(sample_entity_profile: EntityProfile) -> None:
    assert sample_entity_profile.entity_id == "ent-001"
    assert sample_entity_profile.entity_name == "Biscuit"
    assert sample_entity_profile.entity_type == "pet"
    assert sample_entity_profile.product == "jimigpt"
    assert sample_entity_profile.primary_archetype == "chaos_gremlin"


def test_entity_profile_optional_fields_defaults(
    sample_entity_profile: EntityProfile,
) -> None:
    assert sample_entity_profile.secondary_archetype is None
    assert sample_entity_profile.archetype_weights == {}
    assert sample_entity_profile.forbidden_phrases == []
    assert sample_entity_profile.forbidden_topics == []


def test_entity_profile_with_forbidden_content(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> None:
    profile = EntityProfile(
        entity_id="ent-002",
        entity_name="Biscuit",
        entity_type="pet",
        product="jimigpt",
        communication=sample_communication_style,
        emotional=sample_emotional_disposition,
        relational=sample_relational_stance,
        knowledge=sample_knowledge_awareness,
        primary_archetype="chaos_gremlin",
        secondary_archetype="loyal_shadow",
        archetype_weights={"chaos_gremlin": 0.7, "loyal_shadow": 0.3},
        forbidden_phrases=["As an AI", "I understand how you feel"],
        forbidden_topics=["veterinary advice"],
    )
    assert profile.secondary_archetype == "loyal_shadow"
    assert profile.archetype_weights == {"chaos_gremlin": 0.7, "loyal_shadow": 0.3}
    assert "As an AI" in profile.forbidden_phrases
    assert "veterinary advice" in profile.forbidden_topics


def test_entity_profile_missing_required_field(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> None:
    with pytest.raises(ValidationError):
        EntityProfile(
            # entity_id missing
            entity_name="Biscuit",
            entity_type="pet",
            product="jimigpt",
            communication=sample_communication_style,
            emotional=sample_emotional_disposition,
            relational=sample_relational_stance,
            knowledge=sample_knowledge_awareness,
            primary_archetype="chaos_gremlin",
        )


# ---------------------------------------------------------------------------
# EnergyLevel enum
# ---------------------------------------------------------------------------


def test_energy_level_values() -> None:
    assert EnergyLevel.LOW == "low"
    assert EnergyLevel.MEDIUM == "medium"
    assert EnergyLevel.HIGH == "high"
    assert EnergyLevel.VARIABLE == "variable"

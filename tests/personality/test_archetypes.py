"""Tests for archetype config loading and listing."""

from pathlib import Path

import pytest

from src.personality.archetypes import (
    ArchetypeConfig,
    blend_archetypes,
    list_archetypes,
    load_archetype,
)
from src.personality.enums import EnergyLevel
from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    EntityProfile,
    KnowledgeAwareness,
    RelationalStance,
)

ARCHETYPES_DIR = Path(__file__).parent.parent.parent / "config" / "archetypes"
CHAOS_GREMLIN_PATH = ARCHETYPES_DIR / "jimigpt" / "chaos_gremlin.yaml"


# ---------------------------------------------------------------------------
# load_archetype — valid file
# ---------------------------------------------------------------------------


def test_load_archetype_returns_archetype_config() -> None:
    result = load_archetype(CHAOS_GREMLIN_PATH)
    assert isinstance(result, ArchetypeConfig)


def test_load_archetype_id() -> None:
    result = load_archetype(CHAOS_GREMLIN_PATH)
    assert result.id == "jimigpt:chaos_gremlin"


def test_load_archetype_name_and_description() -> None:
    result = load_archetype(CHAOS_GREMLIN_PATH)
    assert result.name == "The Chaos Gremlin"
    assert "energetic" in result.description.lower()


def test_load_archetype_communication_style() -> None:
    result = load_archetype(CHAOS_GREMLIN_PATH)
    assert isinstance(result.communication, CommunicationStyle)
    assert result.communication.energy_level == EnergyLevel.HIGH
    assert result.communication.sentence_length == "short"
    assert len(result.communication.quirks) == 3


def test_load_archetype_emotional_disposition() -> None:
    result = load_archetype(CHAOS_GREMLIN_PATH)
    assert isinstance(result.emotional, EmotionalDisposition)
    assert result.emotional.baseline_mood == "playful"
    assert result.emotional.humor_style == "silly"


def test_load_archetype_relational_stance() -> None:
    result = load_archetype(CHAOS_GREMLIN_PATH)
    assert isinstance(result.relational, RelationalStance)
    assert result.relational.attachment_style == "clingy"


def test_load_archetype_knowledge_awareness() -> None:
    result = load_archetype(CHAOS_GREMLIN_PATH)
    assert isinstance(result.knowledge, KnowledgeAwareness)
    assert result.knowledge.temporal_awareness is True
    assert "food and treats" in result.knowledge.domain_knowledge


def test_load_archetype_forbidden_content() -> None:
    result = load_archetype(CHAOS_GREMLIN_PATH)
    assert "As an AI" in result.forbidden_phrases
    assert "veterinary advice" in result.forbidden_topics


# ---------------------------------------------------------------------------
# load_archetype — error cases
# ---------------------------------------------------------------------------


def test_load_archetype_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_archetype(Path("config/archetypes/jimigpt/does_not_exist.yaml"))


def test_load_archetype_invalid_yaml(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("id: [unclosed bracket\nname: oops")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_archetype(bad_yaml)


def test_load_archetype_invalid_schema(tmp_path: Path) -> None:
    # Valid YAML but missing required fields
    incomplete = tmp_path / "incomplete.yaml"
    incomplete.write_text("id: jimigpt:test\nname: Test")
    with pytest.raises(ValueError, match="Invalid archetype schema"):
        load_archetype(incomplete)


# ---------------------------------------------------------------------------
# list_archetypes
# ---------------------------------------------------------------------------


def test_list_archetypes_returns_list() -> None:
    result = list_archetypes("jimigpt", config_dir=ARCHETYPES_DIR)
    assert isinstance(result, list)


def test_list_archetypes_contains_chaos_gremlin() -> None:
    result = list_archetypes("jimigpt", config_dir=ARCHETYPES_DIR)
    ids = [a.id for a in result]
    assert "jimigpt:chaos_gremlin" in ids


def test_list_archetypes_all_are_archetype_configs() -> None:
    result = list_archetypes("jimigpt", config_dir=ARCHETYPES_DIR)
    assert all(isinstance(a, ArchetypeConfig) for a in result)


def test_list_archetypes_unknown_product_returns_empty() -> None:
    result = list_archetypes("unknown_product", config_dir=ARCHETYPES_DIR)
    assert result == []


# ---------------------------------------------------------------------------
# All 8 archetypes — parametrized validation
# ---------------------------------------------------------------------------

ALL_ARCHETYPE_IDS = [
    "jimigpt:chaos_gremlin",
    "jimigpt:loyal_shadow",
    "jimigpt:regal_one",
    "jimigpt:gentle_soul",
    "jimigpt:food_monster",
    "jimigpt:adventure_buddy",
    "jimigpt:couch_potato",
    "jimigpt:anxious_sweetheart",
]


@pytest.mark.parametrize("archetype_id", ALL_ARCHETYPE_IDS)
def test_all_archetypes_load_and_validate(archetype_id: str) -> None:
    slug = archetype_id.split(":")[1]
    path = ARCHETYPES_DIR / "jimigpt" / f"{slug}.yaml"
    result = load_archetype(path)

    assert isinstance(result, ArchetypeConfig)
    assert result.id == archetype_id
    assert result.name
    assert result.description
    assert isinstance(result.communication, CommunicationStyle)
    assert isinstance(result.emotional, EmotionalDisposition)
    assert isinstance(result.relational, RelationalStance)
    assert isinstance(result.knowledge, KnowledgeAwareness)
    assert len(result.knowledge.domain_knowledge) >= 1
    assert len(result.forbidden_phrases) >= 1
    assert len(result.forbidden_topics) >= 1


def test_all_8_archetypes_found_by_list() -> None:
    result = list_archetypes("jimigpt", config_dir=ARCHETYPES_DIR)
    ids = {a.id for a in result}
    assert ids == set(ALL_ARCHETYPE_IDS)


# ---------------------------------------------------------------------------
# blend_archetypes — fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def alpha() -> ArchetypeConfig:
    return ArchetypeConfig(
        id="test:alpha",
        name="Alpha",
        description="Alpha archetype",
        communication=CommunicationStyle(
            sentence_length="short",
            energy_level=EnergyLevel.HIGH,
            emoji_usage="heavy",
            punctuation_style="excited_exclamations",
            vocabulary_level="simple",
            quirks=["quirk_a1", "quirk_shared"],
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
            domain_knowledge=["domain_a", "domain_shared"],
            user_context_fields=["context_a"],
            temporal_awareness=True,
            memory_references=True,
        ),
        forbidden_phrases=["phrase_a"],
        forbidden_topics=["topic_shared"],
    )


@pytest.fixture
def beta() -> ArchetypeConfig:
    return ArchetypeConfig(
        id="test:beta",
        name="Beta",
        description="Beta archetype",
        communication=CommunicationStyle(
            sentence_length="long",
            energy_level=EnergyLevel.LOW,
            emoji_usage="none",
            punctuation_style="calm_periods",
            vocabulary_level="sophisticated",
            quirks=["quirk_b1", "quirk_shared"],
        ),
        emotional=EmotionalDisposition(
            baseline_mood="calm",
            emotional_range="narrow",
            need_expression="subtle",
            humor_style="dry",
        ),
        relational=RelationalStance(
            attachment_style="independent",
            initiative_style="responsive",
            boundary_respect="high",
            warmth_level="cool",
        ),
        knowledge=KnowledgeAwareness(
            domain_knowledge=["domain_b", "domain_shared"],
            user_context_fields=["context_b"],
            temporal_awareness=False,
            memory_references=False,
        ),
        forbidden_phrases=["phrase_b"],
        forbidden_topics=["topic_b", "topic_shared"],
    )


# ---------------------------------------------------------------------------
# blend_archetypes — tests
# ---------------------------------------------------------------------------


def test_blend_archetypes_returns_entity_profile(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 0.7, "test:beta": 0.3})
    assert isinstance(result, EntityProfile)


def test_blend_archetypes_weights_not_summing_raises_value_error(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    with pytest.raises(ValueError, match="[Ww]eights"):
        blend_archetypes(alpha, beta, {"test:alpha": 0.6, "test:beta": 0.3})


def test_blend_archetypes_weight_1_uses_primary_personality(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 1.0, "test:beta": 0.0})
    assert result.communication.sentence_length == alpha.communication.sentence_length
    assert result.communication.energy_level == alpha.communication.energy_level
    assert result.emotional.baseline_mood == alpha.emotional.baseline_mood
    assert result.relational.attachment_style == alpha.relational.attachment_style


def test_blend_archetypes_secondary_dominates_when_weight_higher(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 0.3, "test:beta": 0.7})
    assert result.communication.sentence_length == beta.communication.sentence_length
    assert result.emotional.baseline_mood == beta.emotional.baseline_mood


def test_blend_archetypes_equal_weights_merges_quirks(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 0.5, "test:beta": 0.5})
    assert "quirk_a1" in result.communication.quirks
    assert "quirk_b1" in result.communication.quirks


def test_blend_archetypes_merged_quirks_no_duplicates(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 0.5, "test:beta": 0.5})
    assert result.communication.quirks.count("quirk_shared") == 1


def test_blend_archetypes_merges_domain_knowledge(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 0.5, "test:beta": 0.5})
    assert "domain_a" in result.knowledge.domain_knowledge
    assert "domain_b" in result.knowledge.domain_knowledge
    assert result.knowledge.domain_knowledge.count("domain_shared") == 1


def test_blend_archetypes_merges_forbidden_content(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 0.5, "test:beta": 0.5})
    assert "phrase_a" in result.forbidden_phrases
    assert "phrase_b" in result.forbidden_phrases
    assert result.forbidden_topics.count("topic_shared") == 1


def test_blend_archetypes_primary_archetype_field_set(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 0.7, "test:beta": 0.3})
    assert result.primary_archetype == alpha.id


def test_blend_archetypes_secondary_archetype_field_set(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    result = blend_archetypes(alpha, beta, {"test:alpha": 0.7, "test:beta": 0.3})
    assert result.secondary_archetype == beta.id


def test_blend_archetypes_weights_stored_in_profile(
    alpha: ArchetypeConfig, beta: ArchetypeConfig
) -> None:
    weights = {"test:alpha": 0.7, "test:beta": 0.3}
    result = blend_archetypes(alpha, beta, weights)
    assert result.archetype_weights == weights


def test_blend_archetypes_secondary_none(alpha: ArchetypeConfig) -> None:
    result = blend_archetypes(alpha, None, {"test:alpha": 1.0})
    assert isinstance(result, EntityProfile)
    assert result.primary_archetype == alpha.id
    assert result.secondary_archetype is None
    assert result.communication.sentence_length == alpha.communication.sentence_length


def test_blend_archetypes_secondary_none_invalid_weights(
    alpha: ArchetypeConfig,
) -> None:
    with pytest.raises(ValueError, match="[Ww]eights"):
        blend_archetypes(alpha, None, {"test:alpha": 0.8})

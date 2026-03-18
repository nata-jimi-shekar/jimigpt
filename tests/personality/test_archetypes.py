"""Tests for archetype config loading and listing."""

from pathlib import Path

import pytest

from src.personality.archetypes import ArchetypeConfig, list_archetypes, load_archetype
from src.personality.enums import EnergyLevel
from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
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

"""Integration test: full pipeline YAML → ArchetypeConfig → blend → PetProfile → AssembledPrompt."""

from pathlib import Path

import pytest

from src.personality.archetypes import blend_archetypes, load_archetype
from src.personality.pet_profile import PetProfile
from src.personality.prompt_builder import AssembledPrompt, assemble_prompt

ARCHETYPES_DIR = Path(__file__).parent.parent.parent / "config" / "archetypes"
CHAOS_GREMLIN_PATH = ARCHETYPES_DIR / "jimigpt" / "chaos_gremlin.yaml"
LOYAL_SHADOW_PATH = ARCHETYPES_DIR / "jimigpt" / "loyal_shadow.yaml"

BLEND_WEIGHTS = {"jimigpt:chaos_gremlin": 0.7, "jimigpt:loyal_shadow": 0.3}

MESSAGE_CONTEXT: dict[str, object] = {
    "message_category": "greeting",
    "max_characters": 160,
    "channel": "sms",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def chaos_gremlin():
    return load_archetype(CHAOS_GREMLIN_PATH)


@pytest.fixture(scope="module")
def loyal_shadow():
    return load_archetype(LOYAL_SHADOW_PATH)


@pytest.fixture(scope="module")
def blended_profile(chaos_gremlin, loyal_shadow):
    return blend_archetypes(chaos_gremlin, loyal_shadow, BLEND_WEIGHTS)


@pytest.fixture(scope="module")
def pet_profile(blended_profile):
    return PetProfile(
        **blended_profile.model_dump(),
        species="dog",
        owner_name="Alex",
        pet_nicknames=["Biscuit", "The Destroyer"],
        feeding_times=["08:00", "18:00"],
        walk_times=["07:00", "17:30"],
        story_insights=["steals socks", "afraid of the vacuum cleaner"],
    )


@pytest.fixture(scope="module")
def assembled(pet_profile):
    return assemble_prompt(pet_profile, MESSAGE_CONTEXT)


# ---------------------------------------------------------------------------
# Stage 1: YAML → ArchetypeConfig
# ---------------------------------------------------------------------------


def test_chaos_gremlin_loads(chaos_gremlin) -> None:
    assert chaos_gremlin.id == "jimigpt:chaos_gremlin"


def test_loyal_shadow_loads(loyal_shadow) -> None:
    assert loyal_shadow.id == "jimigpt:loyal_shadow"


# ---------------------------------------------------------------------------
# Stage 2: blend → EntityProfile
# ---------------------------------------------------------------------------


def test_blend_produces_entity_profile(blended_profile) -> None:
    from src.personality.models import EntityProfile
    assert isinstance(blended_profile, EntityProfile)


def test_blend_primary_archetype_is_chaos_gremlin(blended_profile) -> None:
    assert blended_profile.primary_archetype == "jimigpt:chaos_gremlin"


def test_blend_secondary_archetype_is_loyal_shadow(blended_profile) -> None:
    assert blended_profile.secondary_archetype == "jimigpt:loyal_shadow"


def test_blend_weights_stored(blended_profile) -> None:
    assert blended_profile.archetype_weights == BLEND_WEIGHTS


def test_blend_dominant_personality_from_chaos_gremlin(blended_profile) -> None:
    # At 70/30 chaos_gremlin dominates — its categorical values should win
    assert blended_profile.communication.energy_level.value == "high"
    assert blended_profile.emotional.baseline_mood == "playful"
    assert blended_profile.relational.attachment_style == "clingy"


def test_blend_domain_knowledge_merged(blended_profile, chaos_gremlin, loyal_shadow) -> None:
    merged = blended_profile.knowledge.domain_knowledge
    for item in chaos_gremlin.knowledge.domain_knowledge:
        assert item in merged
    for item in loyal_shadow.knowledge.domain_knowledge:
        assert item in merged


def test_blend_forbidden_phrases_merged(blended_profile, chaos_gremlin, loyal_shadow) -> None:
    merged = blended_profile.forbidden_phrases
    for phrase in chaos_gremlin.forbidden_phrases:
        assert phrase in merged
    for phrase in loyal_shadow.forbidden_phrases:
        assert phrase in merged


# ---------------------------------------------------------------------------
# Stage 3: EntityProfile → PetProfile
# ---------------------------------------------------------------------------


def test_pet_profile_is_pet_profile(pet_profile) -> None:
    assert isinstance(pet_profile, PetProfile)


def test_pet_profile_inherits_blend_personality(pet_profile, blended_profile) -> None:
    assert pet_profile.primary_archetype == blended_profile.primary_archetype
    assert pet_profile.communication.energy_level == blended_profile.communication.energy_level


def test_pet_profile_pet_fields_set(pet_profile) -> None:
    assert pet_profile.species == "dog"
    assert pet_profile.owner_name == "Alex"
    assert "Biscuit" in pet_profile.pet_nicknames
    assert len(pet_profile.feeding_times) == 2


# ---------------------------------------------------------------------------
# Stage 4: PetProfile → AssembledPrompt
# ---------------------------------------------------------------------------


def test_assembled_prompt_type(assembled) -> None:
    assert isinstance(assembled, AssembledPrompt)


def test_assembled_prompt_has_7_blocks(assembled) -> None:
    assert assembled.block_count == 7


def test_assembled_prompt_not_empty(assembled) -> None:
    assert assembled.system_prompt.strip() != ""


def test_assembled_prompt_no_template_artifacts(assembled) -> None:
    assert "{{" not in assembled.system_prompt
    assert "}}" not in assembled.system_prompt


def test_assembled_prompt_no_empty_blocks(assembled) -> None:
    for block in assembled.blocks:
        assert block.content.strip() != "", f"Block '{block.layer}' is empty"


def test_assembled_prompt_contains_personality_markers(assembled) -> None:
    # chaos_gremlin dominates at 70% — its key traits should surface
    prompt = assembled.system_prompt
    assert "playful" in prompt
    assert "short" in prompt
    assert "high" in prompt


def test_assembled_prompt_forbidden_phrases_in_anti_patterns_only(assembled) -> None:
    anti_block = next(b for b in assembled.blocks if b.layer == "anti_patterns")
    other_blocks = [b for b in assembled.blocks if b.layer != "anti_patterns"]

    # Forbidden phrases must appear in anti_patterns block
    assert anti_block.content.strip() != ""

    # They should not be present as instructions in other blocks
    for phrase in ["As an AI", "I understand how you feel", "I'm here for you"]:
        for block in other_blocks:
            assert phrase not in block.content, (
                f"Forbidden phrase '{phrase}' found in block '{block.layer}'"
            )


def test_assembled_prompt_forbidden_topics_in_anti_patterns(assembled) -> None:
    anti_block = next(b for b in assembled.blocks if b.layer == "anti_patterns")
    assert "veterinary advice" in anti_block.content


def test_assembled_prompt_deterministic(pet_profile) -> None:
    result_a = assemble_prompt(pet_profile, MESSAGE_CONTEXT)
    result_b = assemble_prompt(pet_profile, MESSAGE_CONTEXT)
    assert result_a.system_prompt == result_b.system_prompt

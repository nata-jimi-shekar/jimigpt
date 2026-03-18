"""Tests for PetProfile — pet-specific extension of EntityProfile."""

import pytest
from pydantic import ValidationError

from src.personality.models import EntityProfile
from src.personality.pet_profile import PetProfile

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def full_pet_profile(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> PetProfile:
    return PetProfile(
        entity_id="pet-001",
        entity_name="Biscuit",
        entity_type="pet",
        product="jimigpt",
        communication=sample_communication_style,
        emotional=sample_emotional_disposition,
        relational=sample_relational_stance,
        knowledge=sample_knowledge_awareness,
        primary_archetype="chaos_gremlin",
        # Pet-specific required fields
        species="dog",
        owner_name="Alex",
        # Pet-specific optional fields
        breed="Labrador Retriever",
        age_years=3.5,
        size="large",
        appearance_notes=["one ear always up", "wears blue bandana"],
        story_insights=["steals socks", "afraid of thunder"],
        pet_nicknames=["Biscotti", "Biscuit Boy"],
        feeding_times=["08:00", "18:00"],
        walk_times=["07:00", "17:30"],
        bedtime="22:00",
    )


# ---------------------------------------------------------------------------
# Creation with all fields
# ---------------------------------------------------------------------------


def test_pet_profile_required_fields(full_pet_profile: PetProfile) -> None:
    assert full_pet_profile.species == "dog"
    assert full_pet_profile.owner_name == "Alex"


def test_pet_profile_optional_fields(full_pet_profile: PetProfile) -> None:
    assert full_pet_profile.breed == "Labrador Retriever"
    assert full_pet_profile.age_years == 3.5
    assert full_pet_profile.size == "large"
    assert full_pet_profile.bedtime == "22:00"


def test_pet_profile_list_fields(full_pet_profile: PetProfile) -> None:
    assert full_pet_profile.appearance_notes == ["one ear always up", "wears blue bandana"]
    assert full_pet_profile.story_insights == ["steals socks", "afraid of thunder"]
    assert full_pet_profile.pet_nicknames == ["Biscotti", "Biscuit Boy"]
    assert full_pet_profile.feeding_times == ["08:00", "18:00"]
    assert full_pet_profile.walk_times == ["07:00", "17:30"]


# ---------------------------------------------------------------------------
# Optional fields default correctly
# ---------------------------------------------------------------------------


def test_pet_profile_optional_fields_default_to_none(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> None:
    profile = PetProfile(
        entity_id="pet-002",
        entity_name="Whiskers",
        entity_type="pet",
        product="jimigpt",
        communication=sample_communication_style,
        emotional=sample_emotional_disposition,
        relational=sample_relational_stance,
        knowledge=sample_knowledge_awareness,
        primary_archetype="regal_one",
        species="cat",
        owner_name="Jordan",
    )
    assert profile.breed is None
    assert profile.age_years is None
    assert profile.size is None
    assert profile.bedtime is None


def test_pet_profile_list_fields_default_to_empty(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> None:
    profile = PetProfile(
        entity_id="pet-003",
        entity_name="Whiskers",
        entity_type="pet",
        product="jimigpt",
        communication=sample_communication_style,
        emotional=sample_emotional_disposition,
        relational=sample_relational_stance,
        knowledge=sample_knowledge_awareness,
        primary_archetype="regal_one",
        species="cat",
        owner_name="Jordan",
    )
    assert profile.appearance_notes == []
    assert profile.story_insights == []
    assert profile.pet_nicknames == []
    assert profile.feeding_times == []
    assert profile.walk_times == []


# ---------------------------------------------------------------------------
# Inherits EntityProfile validation
# ---------------------------------------------------------------------------


def test_pet_profile_is_entity_profile(full_pet_profile: PetProfile) -> None:
    assert isinstance(full_pet_profile, EntityProfile)


def test_pet_profile_inherits_entity_profile_fields(full_pet_profile: PetProfile) -> None:
    assert full_pet_profile.entity_id == "pet-001"
    assert full_pet_profile.entity_name == "Biscuit"
    assert full_pet_profile.entity_type == "pet"
    assert full_pet_profile.product == "jimigpt"
    assert full_pet_profile.primary_archetype == "chaos_gremlin"


def test_pet_profile_missing_entity_id_raises(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> None:
    with pytest.raises(ValidationError):
        PetProfile(
            # entity_id missing — inherited required field
            entity_name="Biscuit",
            entity_type="pet",
            product="jimigpt",
            communication=sample_communication_style,
            emotional=sample_emotional_disposition,
            relational=sample_relational_stance,
            knowledge=sample_knowledge_awareness,
            primary_archetype="chaos_gremlin",
            species="dog",
            owner_name="Alex",
        )


def test_pet_profile_invalid_energy_level_raises(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> None:
    invalid_style = {**sample_communication_style, "energy_level": "turbo"}
    with pytest.raises(ValidationError):
        PetProfile(
            entity_id="pet-004",
            entity_name="Biscuit",
            entity_type="pet",
            product="jimigpt",
            communication=invalid_style,
            emotional=sample_emotional_disposition,
            relational=sample_relational_stance,
            knowledge=sample_knowledge_awareness,
            primary_archetype="chaos_gremlin",
            species="dog",
            owner_name="Alex",
        )


def test_pet_profile_missing_species_raises(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> None:
    with pytest.raises(ValidationError):
        PetProfile(
            entity_id="pet-005",
            entity_name="Biscuit",
            entity_type="pet",
            product="jimigpt",
            communication=sample_communication_style,
            emotional=sample_emotional_disposition,
            relational=sample_relational_stance,
            knowledge=sample_knowledge_awareness,
            primary_archetype="chaos_gremlin",
            # species missing
            owner_name="Alex",
        )


def test_pet_profile_missing_owner_name_raises(
    sample_communication_style: dict,
    sample_emotional_disposition: dict,
    sample_relational_stance: dict,
    sample_knowledge_awareness: dict,
) -> None:
    with pytest.raises(ValidationError):
        PetProfile(
            entity_id="pet-006",
            entity_name="Biscuit",
            entity_type="pet",
            product="jimigpt",
            communication=sample_communication_style,
            emotional=sample_emotional_disposition,
            relational=sample_relational_stance,
            knowledge=sample_knowledge_awareness,
            primary_archetype="chaos_gremlin",
            species="dog",
            # owner_name missing
        )

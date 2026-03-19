"""Tests for ToneSpectrum defaults and intent weights on archetypes."""

from pathlib import Path

import pytest

from src.messaging.models import MessageIntent
from src.personality.archetypes import ArchetypeConfig, load_archetype
from src.personality.models import ToneSpectrum

ARCHETYPES_DIR = Path(__file__).parent.parent.parent / "config" / "archetypes"
JIMIGPT_DIR = ARCHETYPES_DIR / "jimigpt"

ALL_ARCHETYPE_SLUGS = [
    "chaos_gremlin",
    "loyal_shadow",
    "regal_one",
    "gentle_soul",
    "food_monster",
    "adventure_buddy",
    "couch_potato",
    "anxious_sweetheart",
]

VALID_INTENT_VALUES = {i.value for i in MessageIntent}


# ---------------------------------------------------------------------------
# ToneSpectrum model validation
# ---------------------------------------------------------------------------


def test_tone_spectrum_valid() -> None:
    tone = ToneSpectrum(
        warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
    )
    assert tone.warmth == 0.8
    assert tone.energy == 0.95


def test_tone_spectrum_rejects_out_of_range() -> None:
    with pytest.raises(Exception):
        ToneSpectrum(
            warmth=1.5, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
        )


def test_tone_spectrum_accepts_boundary_values() -> None:
    tone = ToneSpectrum(
        warmth=0.0, humor=1.0, directness=0.0, gravity=1.0, energy=0.0, vulnerability=1.0
    )
    assert tone.warmth == 0.0
    assert tone.humor == 1.0


# ---------------------------------------------------------------------------
# MessageIntent enum
# ---------------------------------------------------------------------------


def test_message_intent_has_expected_values() -> None:
    assert MessageIntent.ENERGIZE == "energize"
    assert MessageIntent.COMFORT == "comfort"
    assert MessageIntent.AFFIRM == "affirm"
    assert MessageIntent.SURPRISE == "surprise"


def test_message_intent_has_14_values() -> None:
    assert len(MessageIntent) == 14


# ---------------------------------------------------------------------------
# ArchetypeConfig loads tone_defaults and intent_weights
# ---------------------------------------------------------------------------


def test_chaos_gremlin_has_tone_defaults() -> None:
    archetype = load_archetype(JIMIGPT_DIR / "chaos_gremlin.yaml")
    assert archetype.tone_defaults is not None
    assert isinstance(archetype.tone_defaults, ToneSpectrum)


def test_chaos_gremlin_tone_values_match_spec() -> None:
    archetype = load_archetype(JIMIGPT_DIR / "chaos_gremlin.yaml")
    tone = archetype.tone_defaults
    assert tone is not None
    assert tone.humor >= 0.8       # chaos_gremlin: high humor
    assert tone.energy >= 0.8      # high energy
    assert tone.gravity <= 0.2     # low gravity


def test_loyal_shadow_tone_values_match_spec() -> None:
    archetype = load_archetype(JIMIGPT_DIR / "loyal_shadow.yaml")
    tone = archetype.tone_defaults
    assert tone is not None
    assert tone.warmth >= 0.8      # loyal_shadow: high warmth
    assert tone.vulnerability >= 0.7  # high vulnerability
    assert tone.energy <= 0.5     # low energy


def test_chaos_gremlin_has_intent_weights() -> None:
    archetype = load_archetype(JIMIGPT_DIR / "chaos_gremlin.yaml")
    assert archetype.intent_weights
    assert isinstance(archetype.intent_weights, dict)


def test_intent_weights_keys_are_valid_intents() -> None:
    archetype = load_archetype(JIMIGPT_DIR / "chaos_gremlin.yaml")
    for key in archetype.intent_weights:
        assert key in VALID_INTENT_VALUES, f"'{key}' is not a valid MessageIntent"


def test_intent_weights_values_in_range() -> None:
    archetype = load_archetype(JIMIGPT_DIR / "chaos_gremlin.yaml")
    for key, value in archetype.intent_weights.items():
        assert 0.0 <= value <= 1.0, f"Weight for '{key}' out of range: {value}"


# ---------------------------------------------------------------------------
# Intent weights sum to 1.0 — parametrized across all 8 archetypes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", ALL_ARCHETYPE_SLUGS)
def test_intent_weights_sum_to_1(slug: str) -> None:
    archetype = load_archetype(JIMIGPT_DIR / f"{slug}.yaml")
    total = sum(archetype.intent_weights.values())
    assert abs(total - 1.0) < 0.001, (
        f"{slug} intent_weights sum to {total:.4f}, expected 1.0"
    )


# ---------------------------------------------------------------------------
# All 8 archetypes have tone_defaults and intent_weights
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", ALL_ARCHETYPE_SLUGS)
def test_all_archetypes_have_tone_defaults(slug: str) -> None:
    archetype = load_archetype(JIMIGPT_DIR / f"{slug}.yaml")
    assert archetype.tone_defaults is not None
    assert isinstance(archetype.tone_defaults, ToneSpectrum)


@pytest.mark.parametrize("slug", ALL_ARCHETYPE_SLUGS)
def test_all_archetypes_tone_values_in_range(slug: str) -> None:
    archetype = load_archetype(JIMIGPT_DIR / f"{slug}.yaml")
    tone = archetype.tone_defaults
    assert tone is not None
    for field in ("warmth", "humor", "directness", "gravity", "energy", "vulnerability"):
        value = getattr(tone, field)
        assert 0.0 <= value <= 1.0, f"{slug}.{field} = {value} out of range"


@pytest.mark.parametrize("slug", ALL_ARCHETYPE_SLUGS)
def test_all_archetypes_have_intent_weights(slug: str) -> None:
    archetype = load_archetype(JIMIGPT_DIR / f"{slug}.yaml")
    assert archetype.intent_weights, f"{slug} has empty intent_weights"

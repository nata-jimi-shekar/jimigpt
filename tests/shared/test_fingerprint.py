"""Tests for personality fingerprinting and drift detection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.shared.fingerprint import (
    DriftDetection,
    PersonalityFingerprint,
    compare_fingerprints,
    extract_fingerprint,
)

UTC = timezone.utc
NOW = datetime(2026, 3, 24, 10, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# PersonalityFingerprint model
# ---------------------------------------------------------------------------


class TestPersonalityFingerprint:
    def test_validates_correctly(self) -> None:
        fp = PersonalityFingerprint(
            archetype_id="chaos_gremlin",
            model_id="claude-haiku-4-5",
            generated_at=NOW,
            avg_message_length=60.0,
            exclamation_rate=2.5,
            emoji_rate=1.2,
            caps_word_rate=0.8,
            question_rate=0.3,
            avg_sentence_length=8.0,
            vocabulary_diversity=0.7,
            energy_proxy=0.9,
            warmth_proxy=0.5,
            humor_proxy=0.7,
        )
        assert fp.archetype_id == "chaos_gremlin"
        assert fp.energy_proxy == 0.9


# ---------------------------------------------------------------------------
# DriftDetection model
# ---------------------------------------------------------------------------


class TestDriftDetection:
    def test_validates_correctly(self) -> None:
        dd = DriftDetection(
            archetype_id="chaos_gremlin",
            model_a="claude-haiku-4-5",
            model_b="claude-sonnet-4-6",
            drift_score=0.05,
            dimensions_drifted=[],
            alert_level="none",
        )
        assert dd.drift_score == 0.05
        assert dd.alert_level == "none"


# ---------------------------------------------------------------------------
# extract_fingerprint — linguistic feature extraction
# ---------------------------------------------------------------------------


class TestExtractFingerprint:
    def test_high_energy_messages_produce_high_energy_proxy(self) -> None:
        messages = [
            "WAKE UP! It's time to PLAY!! 🎉🎉🎉",
            "LET'S GO!! BEST DAY EVER!!! 🐾💥",
            "ZOOM ZOOM ZOOM!!! SO EXCITED!!! 🚀🚀",
        ]
        fp = extract_fingerprint(messages, archetype_id="chaos_gremlin", model_id="m1")
        assert fp.energy_proxy > 0.5

    def test_calm_messages_produce_low_energy_proxy(self) -> None:
        messages = [
            "Thinking of you today.",
            "Hope you have a peaceful afternoon.",
            "I am here whenever you need me.",
        ]
        fp = extract_fingerprint(messages, archetype_id="loyal_shadow", model_id="m1")
        assert fp.energy_proxy < 0.4

    def test_emoji_heavy_messages_produce_high_emoji_rate(self) -> None:
        messages = [
            "Hi 😊😊😊😊😊",
            "Love you 💕💕💕💕",
            "Yay! 🎉🎉🎉🎉🎉",
        ]
        fp = extract_fingerprint(messages, archetype_id="chaos_gremlin", model_id="m1")
        assert fp.emoji_rate > 1.0

    def test_no_emoji_messages_produce_zero_emoji_rate(self) -> None:
        messages = [
            "Good morning.",
            "How are you today?",
            "Take care.",
        ]
        fp = extract_fingerprint(messages, archetype_id="regal_one", model_id="m1")
        assert fp.emoji_rate == 0.0

    def test_question_heavy_produces_high_question_rate(self) -> None:
        messages = [
            "How are you? Did you eat? Are you okay?",
            "What did you do today? How was work?",
            "Feeling good? Did you rest?",
        ]
        fp = extract_fingerprint(messages, archetype_id="anxious_sweetheart", model_id="m1")
        assert fp.question_rate > 1.0

    def test_avg_message_length_computed(self) -> None:
        messages = ["Hello!", "Good morning, hope you slept well!"]
        fp = extract_fingerprint(messages, archetype_id="gentle_soul", model_id="m1")
        expected = (len("Hello!") + len("Good morning, hope you slept well!")) / 2
        assert abs(fp.avg_message_length - expected) < 0.01

    def test_vocabulary_diversity_between_0_and_1(self) -> None:
        messages = ["the cat sat on the mat", "the dog ran in the park"]
        fp = extract_fingerprint(messages, archetype_id="couch_potato", model_id="m1")
        assert 0.0 <= fp.vocabulary_diversity <= 1.0

    def test_all_same_words_produces_low_diversity(self) -> None:
        messages = ["woof woof woof", "woof woof woof", "woof woof woof"]
        fp = extract_fingerprint(messages, archetype_id="chaos_gremlin", model_id="m1")
        assert fp.vocabulary_diversity < 0.3

    def test_empty_messages_handled_gracefully(self) -> None:
        fp = extract_fingerprint([], archetype_id="chaos_gremlin", model_id="m1")
        assert fp.avg_message_length == 0.0
        assert fp.energy_proxy == 0.0

    def test_returns_personality_fingerprint(self) -> None:
        fp = extract_fingerprint(["Hello!"], archetype_id="chaos_gremlin", model_id="m1")
        assert isinstance(fp, PersonalityFingerprint)

    def test_archetype_and_model_stored(self) -> None:
        fp = extract_fingerprint(["Hi!"], archetype_id="food_monster", model_id="claude-haiku-4-5")
        assert fp.archetype_id == "food_monster"
        assert fp.model_id == "claude-haiku-4-5"


# ---------------------------------------------------------------------------
# compare_fingerprints — drift detection
# ---------------------------------------------------------------------------


def _make_fp(
    archetype: str = "chaos_gremlin",
    model: str = "m1",
    *,
    energy: float = 0.5,
    warmth: float = 0.5,
    humor: float = 0.5,
    exclamation_rate: float = 1.0,
    emoji_rate: float = 0.5,
    caps_word_rate: float = 0.3,
    question_rate: float = 0.3,
    avg_message_length: float = 60.0,
    avg_sentence_length: float = 10.0,
    vocabulary_diversity: float = 0.6,
) -> PersonalityFingerprint:
    return PersonalityFingerprint(
        archetype_id=archetype,
        model_id=model,
        generated_at=NOW,
        avg_message_length=avg_message_length,
        exclamation_rate=exclamation_rate,
        emoji_rate=emoji_rate,
        caps_word_rate=caps_word_rate,
        question_rate=question_rate,
        avg_sentence_length=avg_sentence_length,
        vocabulary_diversity=vocabulary_diversity,
        energy_proxy=energy,
        warmth_proxy=warmth,
        humor_proxy=humor,
    )


class TestCompareFingerprints:
    def test_identical_fingerprints_produce_near_zero_drift(self) -> None:
        fp = _make_fp()
        result = compare_fingerprints(fp, fp)
        assert result.drift_score < 0.05

    def test_very_different_fingerprints_produce_high_drift(self) -> None:
        fp_a = _make_fp(energy=0.95, warmth=0.1, humor=0.9, exclamation_rate=3.0,
                        emoji_rate=2.5, caps_word_rate=1.5)
        fp_b = _make_fp(energy=0.05, warmth=0.9, humor=0.1, exclamation_rate=0.0,
                        emoji_rate=0.0, caps_word_rate=0.0)
        result = compare_fingerprints(fp_a, fp_b)
        assert result.drift_score > 0.3

    def test_returns_drift_detection(self) -> None:
        fp = _make_fp()
        result = compare_fingerprints(fp, fp)
        assert isinstance(result, DriftDetection)

    def test_model_ids_recorded(self) -> None:
        fp_a = _make_fp(model="claude-haiku-4-5")
        fp_b = _make_fp(model="claude-sonnet-4-6")
        result = compare_fingerprints(fp_a, fp_b)
        assert result.model_a == "claude-haiku-4-5"
        assert result.model_b == "claude-sonnet-4-6"

    def test_alert_level_none_for_low_drift(self) -> None:
        fp = _make_fp()
        result = compare_fingerprints(fp, fp)
        assert result.alert_level == "none"

    def test_alert_level_critical_for_high_drift(self) -> None:
        fp_a = _make_fp(energy=1.0, warmth=0.0, humor=1.0, exclamation_rate=5.0)
        fp_b = _make_fp(energy=0.0, warmth=1.0, humor=0.0, exclamation_rate=0.0)
        result = compare_fingerprints(fp_a, fp_b)
        assert result.alert_level in ("warning", "critical")

    def test_dimensions_drifted_empty_for_identical(self) -> None:
        fp = _make_fp()
        result = compare_fingerprints(fp, fp)
        assert result.dimensions_drifted == []

    def test_dimensions_drifted_populated_for_large_difference(self) -> None:
        fp_a = _make_fp(energy=0.9)
        fp_b = _make_fp(energy=0.1)
        result = compare_fingerprints(fp_a, fp_b)
        assert "energy_proxy" in result.dimensions_drifted

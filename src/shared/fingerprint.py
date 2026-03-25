"""Personality fingerprinting for model drift detection.

extract_fingerprint() computes linguistic features from a message set.
compare_fingerprints() measures how much two fingerprints diverge.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Warm and humor word sets
# ---------------------------------------------------------------------------

_WARM_WORDS = {
    "love", "miss", "cuddle", "hug", "care", "heart", "warm", "sweet",
    "dear", "precious", "adore", "cherish", "comfort", "gentle", "kind",
}

_HUMOR_MARKERS = {
    "heh", "lol", "haha", "joke", "silly", "goofy", "hilarious", "funny",
    "tease", "wink", "snort", "giggle", "cheeky",
}

# Emoji detection: characters in typical emoji Unicode ranges
_EMOJI_RE = re.compile(
    "[\U00010000-\U0010ffff"
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\u2600-\u27BF"
    "\u2300-\u23FF"
    "]",
    flags=re.UNICODE,
)

# Sentence boundary splitting
_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")

# Normalization ranges for drift score calculation
_FEATURE_RANGES: dict[str, float] = {
    "avg_message_length": 200.0,
    "exclamation_rate": 5.0,
    "emoji_rate": 5.0,
    "caps_word_rate": 3.0,
    "question_rate": 3.0,
    "avg_sentence_length": 30.0,
    "vocabulary_diversity": 1.0,
    "energy_proxy": 1.0,
    "warmth_proxy": 1.0,
    "humor_proxy": 1.0,
}

# Dimension drift threshold — feature difference (normalized) above which
# it is listed in dimensions_drifted
_DRIFT_DIMENSION_THRESHOLD = 0.15


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class PersonalityFingerprint(BaseModel):
    """Measurable personality signature for drift detection."""

    archetype_id: str
    model_id: str
    generated_at: datetime

    avg_message_length: float
    exclamation_rate: float      # Exclamations per message
    emoji_rate: float            # Emoji per message
    caps_word_rate: float        # ALL-CAPS words per message
    question_rate: float         # Question marks per message
    avg_sentence_length: float   # Average words per sentence
    vocabulary_diversity: float  # Unique words / total words

    energy_proxy: float          # Derived from caps, exclamations, emoji
    warmth_proxy: float          # Derived from warm word presence
    humor_proxy: float           # Derived from humor markers


class DriftDetection(BaseModel):
    """Comparison between two fingerprints."""

    archetype_id: str
    model_a: str
    model_b: str
    drift_score: float            # 0.0 = identical, 1.0 = completely different
    dimensions_drifted: list[str]  # Features that changed significantly
    alert_level: str              # "none" | "notice" | "warning" | "critical"


# ---------------------------------------------------------------------------
# Feature extraction helpers
# ---------------------------------------------------------------------------


def _count_emoji(text: str) -> int:
    return len(_EMOJI_RE.findall(text))


def _count_caps_words(text: str) -> int:
    return sum(1 for w in text.split() if w.isupper() and len(w) > 1)


def _count_warm_words(text: str) -> int:
    words = re.findall(r"[a-z]+", text.lower())
    return sum(1 for w in words if w in _WARM_WORDS)


def _count_humor_markers(text: str) -> int:
    words = re.findall(r"[a-z]+", text.lower())
    return sum(1 for w in words if w in _HUMOR_MARKERS)


def _avg_sentence_length(messages: list[str]) -> float:
    lengths: list[int] = []
    for msg in messages:
        sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(msg) if s.strip()]
        for sent in sentences:
            word_count = len(sent.split())
            if word_count > 0:
                lengths.append(word_count)
    return sum(lengths) / len(lengths) if lengths else 0.0


def _vocabulary_diversity(messages: list[str]) -> float:
    all_words = re.findall(r"[a-z]+", " ".join(messages).lower())
    if not all_words:
        return 0.0
    return len(set(all_words)) / len(all_words)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_fingerprint(
    messages: list[str],
    *,
    archetype_id: str,
    model_id: str,
    generated_at: datetime | None = None,
) -> PersonalityFingerprint:
    """Compute a personality fingerprint from a list of messages."""
    if not messages:
        return PersonalityFingerprint(
            archetype_id=archetype_id,
            model_id=model_id,
            generated_at=generated_at or datetime.now(tz=timezone.utc),
            avg_message_length=0.0,
            exclamation_rate=0.0,
            emoji_rate=0.0,
            caps_word_rate=0.0,
            question_rate=0.0,
            avg_sentence_length=0.0,
            vocabulary_diversity=0.0,
            energy_proxy=0.0,
            warmth_proxy=0.0,
            humor_proxy=0.0,
        )

    n = len(messages)

    avg_len = sum(len(m) for m in messages) / n
    excl_rate = sum(m.count("!") for m in messages) / n
    emoji_rate = sum(_count_emoji(m) for m in messages) / n
    caps_rate = sum(_count_caps_words(m) for m in messages) / n
    q_rate = sum(m.count("?") for m in messages) / n
    avg_sent_len = _avg_sentence_length(messages)
    vocab_div = _vocabulary_diversity(messages)
    warm_count = sum(_count_warm_words(m) for m in messages) / n
    humor_count = sum(_count_humor_markers(m) for m in messages) / n

    energy = min(1.0, (
        min(excl_rate / 3.0, 1.0) * 0.4
        + min(caps_rate / 2.0, 1.0) * 0.35
        + min(emoji_rate / 3.0, 1.0) * 0.25
    ))
    warmth = min(1.0, warm_count / 2.0)
    humor = min(1.0, humor_count / 1.5 + min(emoji_rate / 5.0, 0.3))

    return PersonalityFingerprint(
        archetype_id=archetype_id,
        model_id=model_id,
        generated_at=generated_at or datetime.now(tz=timezone.utc),
        avg_message_length=avg_len,
        exclamation_rate=excl_rate,
        emoji_rate=emoji_rate,
        caps_word_rate=caps_rate,
        question_rate=q_rate,
        avg_sentence_length=avg_sent_len,
        vocabulary_diversity=vocab_div,
        energy_proxy=energy,
        warmth_proxy=warmth,
        humor_proxy=humor,
    )


def compare_fingerprints(
    a: PersonalityFingerprint,
    b: PersonalityFingerprint,
    *,
    allow_cross_archetype: bool = False,
) -> DriftDetection:
    """Compute drift between two fingerprints for the same archetype.

    Raises ValueError if archetypes differ, unless allow_cross_archetype=True.
    """
    if not allow_cross_archetype and a.archetype_id != b.archetype_id:
        raise ValueError(
            f"Cannot compare fingerprints for different archetypes: "
            f"{a.archetype_id!r} vs {b.archetype_id!r}. "
            f"Pass allow_cross_archetype=True to override."
        )
    features = list(_FEATURE_RANGES.keys())
    diffs: dict[str, float] = {}

    for feat in features:
        val_a: float = getattr(a, feat)
        val_b: float = getattr(b, feat)
        norm_range = _FEATURE_RANGES[feat]
        diffs[feat] = abs(val_a - val_b) / norm_range

    drift_score = round(sum(diffs.values()) / len(diffs), 4)
    dimensions_drifted = [f for f, d in diffs.items() if d > _DRIFT_DIMENSION_THRESHOLD]

    if drift_score < 0.1:
        alert_level = "none"
    elif drift_score < 0.2:
        alert_level = "notice"
    elif drift_score < 0.4:
        alert_level = "warning"
    else:
        alert_level = "critical"

    return DriftDetection(
        archetype_id=a.archetype_id,
        model_a=a.model_id,
        model_b=b.model_id,
        drift_score=drift_score,
        dimensions_drifted=dimensions_drifted,
        alert_level=alert_level,
    )

"""Quality gate — evaluates generated messages before delivery.

Each check is a pure function.  QualityGate runs only the checks it is
configured with; all must pass for the result to be passed=True.

Foundation (Phase 2):
  CONSECUTIVE_COHERENCE is implemented as a simple rule-based check in Phase 1:
  COMFORT → ENERGIZE is flagged as emotionally jarring.
  In Phase 2 this becomes arc-coherence-aware: the check understands
  which arc the message belongs to and whether the emotional shift is
  intentional (e.g., arc position 3/5 deliberately lifts the mood).
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.messaging.composer import MessageComposition
from src.messaging.models import MessageIntent

if TYPE_CHECKING:
    from src.messaging.generator import GeneratedMessage

# ---------------------------------------------------------------------------
# Character-breaking phrases (entity must never reveal it is an AI)
# ---------------------------------------------------------------------------
_AI_BREAKING_PHRASES = [
    "language model",
    "large language model",
    "i was trained",
    "neural network",
    "i am a bot",
    "i am an ai",
    "artificial intelligence",
]

# ---------------------------------------------------------------------------
# Safety: phrases that should never appear in any message
# ---------------------------------------------------------------------------
_UNSAFE_PHRASES = [
    "kill yourself",
    "you should die",
    "end your life",
    "commit suicide",
    "hurt yourself",
]

# ---------------------------------------------------------------------------
# CONSECUTIVE_COHERENCE: intent pairs that are emotionally jarring
# Phase 1: simple table.  Phase 2: arc-position-aware.
# ---------------------------------------------------------------------------
_JARRING_TRANSITIONS: set[tuple[MessageIntent, MessageIntent]] = {
    (MessageIntent.COMFORT, MessageIntent.ENERGIZE),
    (MessageIntent.COMFORT, MessageIntent.SURPRISE),
    (MessageIntent.GROUND, MessageIntent.ENERGIZE),
    (MessageIntent.GROUND, MessageIntent.SURPRISE),
}


class QualityCheck(StrEnum):
    CHARACTER_CONSISTENCY = "character_consistency"
    REPETITION = "repetition"
    TONE_MATCH = "tone_match"
    CONTENT_BOUNDARY = "content_boundary"
    LENGTH = "length"
    SAFETY = "safety"
    FORBIDDEN_PHRASES = "forbidden_phrases"
    INTENT_ALIGNMENT = "intent_alignment"
    # Foundation: Phase 1 basic; Phase 2 arc-coherence-aware
    CONSECUTIVE_COHERENCE = "consecutive_coherence"


class QualityResult(BaseModel):
    passed: bool
    checks_run: list[QualityCheck]
    checks_failed: list[QualityCheck]
    failure_reasons: list[str]


class QualityGate:
    """Configurable quality gate — runs only the checks it is initialised with."""

    def __init__(self, checks: list[QualityCheck]) -> None:
        self._checks = checks

    def evaluate(
        self,
        message: GeneratedMessage,
        composition: MessageComposition,
        *,
        previous_message: GeneratedMessage | None = None,
    ) -> QualityResult:
        """Run all configured checks.  Returns passed=True only if all pass."""
        failed: list[QualityCheck] = []
        reasons: list[str] = []

        for check in self._checks:
            ok, reason = _run_check(check, message, composition, previous_message)
            if not ok:
                failed.append(check)
                reasons.append(reason)

        return QualityResult(
            passed=len(failed) == 0,
            checks_run=list(self._checks),
            checks_failed=failed,
            failure_reasons=reasons,
        )


# ---------------------------------------------------------------------------
# Check dispatcher
# ---------------------------------------------------------------------------


def _run_check(
    check: QualityCheck,
    message: GeneratedMessage,
    composition: MessageComposition,
    previous_message: GeneratedMessage | None,
) -> tuple[bool, str]:
    """Return (passed, failure_reason).  failure_reason is '' when passed."""
    match check:
        case QualityCheck.LENGTH:
            return _check_length(message, composition)
        case QualityCheck.FORBIDDEN_PHRASES:
            return _check_forbidden_phrases(message, composition)
        case QualityCheck.CHARACTER_CONSISTENCY:
            return _check_character_consistency(message)
        case QualityCheck.CONTENT_BOUNDARY:
            return _check_content_boundary(message, composition)
        case QualityCheck.REPETITION:
            return _check_repetition(message, composition)
        case QualityCheck.SAFETY:
            return _check_safety(message)
        case QualityCheck.TONE_MATCH:
            return _check_tone_match(message, composition)
        case QualityCheck.INTENT_ALIGNMENT:
            return _check_intent_alignment(message, composition)
        case QualityCheck.CONSECUTIVE_COHERENCE:
            return _check_consecutive_coherence(message, composition, previous_message)
        case _:
            return True, ""


# ---------------------------------------------------------------------------
# Individual check implementations
# ---------------------------------------------------------------------------


def _check_length(
    message: GeneratedMessage, composition: MessageComposition
) -> tuple[bool, str]:
    if message.character_count > composition.max_characters:
        return (
            False,
            f"Message is {message.character_count} characters, "
            f"exceeds limit of {composition.max_characters}.",
        )
    return True, ""


def _check_forbidden_phrases(
    message: GeneratedMessage, composition: MessageComposition
) -> tuple[bool, str]:
    content_lower = message.content.lower()
    for phrase in composition.entity_voice.forbidden_phrases:
        if phrase.lower() in content_lower:
            return False, f'Forbidden phrase detected: "{phrase}".'
    return True, ""


def _check_character_consistency(message: GeneratedMessage) -> tuple[bool, str]:
    content_lower = message.content.lower()
    for phrase in _AI_BREAKING_PHRASES:
        if phrase in content_lower:
            return False, f'Character-breaking phrase detected: "{phrase}".'
    return True, ""


def _check_content_boundary(
    message: GeneratedMessage, composition: MessageComposition
) -> tuple[bool, str]:
    content_lower = message.content.lower()
    for topic in composition.entity_voice.forbidden_topics:
        if topic.lower() in content_lower:
            return False, f'Forbidden topic detected: "{topic}".'
    return True, ""


def _check_repetition(
    message: GeneratedMessage, composition: MessageComposition
) -> tuple[bool, str]:
    for past in composition.recent_messages:
        if message.content.strip() == past.strip():
            return False, "Message is an exact duplicate of a recent message."
    return True, ""


def _check_safety(message: GeneratedMessage) -> tuple[bool, str]:
    content_lower = message.content.lower()
    for phrase in _UNSAFE_PHRASES:
        if phrase in content_lower:
            return False, f'Unsafe content detected: "{phrase}".'
    return True, ""


def _check_tone_match(
    message: GeneratedMessage, composition: MessageComposition
) -> tuple[bool, str]:
    """Flag tone/content mismatch in both directions.

    Direction 1: high-excitement markers when energy spec is very low.
    Direction 2: flat, lifeless content when energy spec is high.
    """
    tone = composition.tone
    content = message.content

    # Direction 1: high excitement contradicts low energy spec
    if tone.energy < 0.3:
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        exclamation_count = content.count("!")
        if caps_ratio > 0.3 and exclamation_count >= 2:
            return (
                False,
                f"High-excitement style (caps ratio {caps_ratio:.2f}, "
                f"{exclamation_count} exclamations) contradicts low energy "
                f"spec ({tone.energy:.2f}).",
            )

    # Direction 2: flat content contradicts high energy spec
    if tone.energy > 0.7:
        has_exclamation = "!" in content
        has_uppercase_word = any(w.isupper() and len(w) > 1 for w in content.split())
        has_emoji = any(ord(c) > 0x1F600 for c in content)
        if not has_exclamation and not has_uppercase_word and not has_emoji:
            return (
                False,
                f"Flat content lacks energy markers (no exclamations, caps, "
                f"or emoji) but energy spec is high ({tone.energy:.2f}).",
            )

    return True, ""


def _check_intent_alignment(
    message: GeneratedMessage, composition: MessageComposition
) -> tuple[bool, str]:
    """Minimal Phase 1 check: content must be non-empty."""
    if not message.content.strip():
        return False, "Empty content cannot align with any intent."
    return True, ""


def _check_consecutive_coherence(
    message: GeneratedMessage,
    composition: MessageComposition,
    previous_message: GeneratedMessage | None,
) -> tuple[bool, str]:
    """Phase 1: flag jarring intent transitions.

    Phase 2: this will be arc-position-aware — a COMFORT→ENERGIZE shift
    at arc position 4/5 (the lift) is intentional and should pass.
    """
    if previous_message is None:
        return True, ""

    prev_intent = previous_message.intended_intent
    curr_intent = composition.intent.primary_intent

    if (prev_intent, curr_intent) in _JARRING_TRANSITIONS:
        return (
            False,
            f"Emotionally jarring transition: {prev_intent.value} → "
            f"{curr_intent.value}. Consider a bridging message.",
        )
    return True, ""

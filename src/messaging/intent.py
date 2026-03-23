"""Message intent selection engine.

Selects the primary emotional intent for a message based on:
  - trigger.message_category  (what kind of message is being sent)
  - context signals           (time of day, sentiment, season)
  - trust_stage               (how well the entity knows the user)
  - archetype_weights         (personality bias toward certain intents)

Foundation (Phase 2):
  - life_contexts param accepted but ignored in Phase 1.
    In Phase 2, active life contexts override intent selection
    (e.g., "user_sick" blocks ENERGIZE and raises COMFORT priority;
    "user_celebrating" raises CELEBRATE weight).
"""

from enum import StrEnum

from pydantic import BaseModel, Field

from src.messaging.models import MessageIntent
from src.messaging.signals import ContextSignalBundle, ContextSignalSource
from src.messaging.triggers import TriggerRule

# Time-of-day values that indicate gentle, low-demand moments.
_QUIET_TIMES = {"early_morning", "late_night", "night"}

# Trust-stage intensity map.  Stranger gets a lighter touch;
# deeper trust allows fuller emotional expression.
_TRUST_INTENSITY: dict[str, float] = {
    "stranger": 0.35,
    "initial": 0.55,
    "working": 0.70,
    "deep": 0.80,
    "alliance": 0.85,
}


class TrustStage(StrEnum):
    """Progressive relationship stages between entity and user.

    STRANGER  — First 24 hours
    INITIAL   — Days 2-7
    WORKING   — Weeks 2-4
    DEEP      — Month 2+
    ALLIANCE  — Month 3+
    """

    STRANGER = "stranger"
    INITIAL = "initial"
    WORKING = "working"
    DEEP = "deep"
    ALLIANCE = "alliance"


class IntentProfile(BaseModel):
    """Selected intent and expression intensity for a single message."""

    primary_intent: MessageIntent
    secondary_intent: MessageIntent | None = None
    intensity: float = Field(ge=0.0, le=1.0)


def select_intent(
    trigger: TriggerRule,
    signals: ContextSignalBundle,
    trust_stage: TrustStage,
    archetype_weights: dict[str, float],
    *,
    life_contexts: list[str] | None = None,  # Foundation: Phase 2 overrides
) -> IntentProfile:
    """Return the IntentProfile that best fits this trigger + context moment.

    Selection order (highest to lowest precedence):
    1. Anniversary signal     → CELEBRATE or SURPRISE
    2. Negative sentiment     → COMFORT (overrides category default)
    3. message_category rules → base intent
    4. Trust-stage intensity
    """
    # --- read relevant signals ---
    sentiment = _get_signal(signals, "interaction:last_response_sentiment")
    time_of_day = _get_signal(signals, "time_of_day")
    day_type = _get_signal(signals, "day_type")
    anniversary = _get_signal(signals, "seasonal:entity_anniversary")

    # 1. Anniversary overrides everything (a special moment)
    if anniversary == "true":
        primary = _archetype_pick(
            archetype_weights,
            preferred=[MessageIntent.CELEBRATE, MessageIntent.SURPRISE],
        )
        return _profile(primary, trust_stage)

    # 2. Negative sentiment overrides category → COMFORT
    if sentiment == "negative":
        return _profile(MessageIntent.COMFORT, trust_stage)

    # 3. Category-based selection
    category = trigger.message_category
    primary = _select_by_category(category, time_of_day, day_type, archetype_weights)

    return _profile(primary, trust_stage)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_signal(bundle: ContextSignalBundle, key: str) -> str | None:
    sig = bundle.get_signal(key)
    return sig.signal_value if sig else None


def _profile(primary: MessageIntent, trust_stage: TrustStage) -> IntentProfile:
    intensity = _TRUST_INTENSITY.get(trust_stage.value, 0.70)
    return IntentProfile(primary_intent=primary, intensity=intensity)


def _archetype_pick(
    weights: dict[str, float],
    preferred: list[MessageIntent],
) -> MessageIntent:
    """Return the highest-weighted intent from the preferred list."""
    return max(preferred, key=lambda i: weights.get(i.value, 0.0))


def _select_by_category(
    category: str,
    time_of_day: str | None,
    day_type: str | None,
    archetype_weights: dict[str, float],
) -> MessageIntent:
    """Map message_category → primary intent using time context."""
    if category == "greeting":
        if time_of_day in _QUIET_TIMES or day_type == "weekend":
            return MessageIntent.ACCOMPANY
        return MessageIntent.ENERGIZE

    if category in ("need", "pet_need"):
        return MessageIntent.REMIND

    if category == "caring":
        return MessageIntent.AFFIRM

    if category == "celebrate":
        return MessageIntent.CELEBRATE

    if category in ("personality_moment", "surprise"):
        return _archetype_pick(
            archetype_weights,
            preferred=[MessageIntent.ENERGIZE, MessageIntent.SURPRISE],
        )

    # Unknown category — use archetype's highest-weighted intent
    best = max(archetype_weights, key=lambda k: archetype_weights[k])
    return MessageIntent(best)

"""Recipient state inference.

Infers the user's likely situational and emotional state from available
context signals.  Phase 1 uses TIME + INTERACTION + SEASONAL signals.

Foundation (Phase 2):
  - life_contexts param accepted but ignored in Phase 1.
    In Phase 2, active life contexts directly influence inferred state:
    e.g., "user_sick" → emotional_context="unwell", likely_energy=low,
    likely_receptivity=low unless the message is comfort-oriented.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from src.messaging.intent import TrustStage
from src.messaging.signals import ContextSignalBundle, ContextSignalSource

# Phase 1 signal sources used for confidence scoring
_PHASE1_SOURCES = {ContextSignalSource.TIME, ContextSignalSource.INTERACTION, ContextSignalSource.SEASONAL}

# Workday hours where the user is likely occupied (morning / midday / afternoon)
_WORK_HOURS = {"morning", "midday", "afternoon"}


class TrustProfile(BaseModel):
    """Current trust relationship between entity and user."""

    user_id: str
    entity_id: str
    current_stage: TrustStage
    stage_entered_at: datetime


class RecipientState(BaseModel):
    """Inferred model of the user's likely situational and emotional state."""

    likely_availability: str = Field(
        description="free | busy | sleeping | commuting | social"
    )
    likely_energy: float = Field(
        ge=0.0, le=1.0,
        description="Inferred energy level. 0.0 = exhausted, 1.0 = highly energetic.",
    )
    likely_receptivity: float = Field(
        ge=0.0, le=1.0,
        description="How open to a message right now. Busy morning = low. Relaxed weekend = high.",
    )
    emotional_context: str = Field(
        description="neutral | positive | stressed | lonely | celebratory | grieving"
    )
    state_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this inference. More signal sources = higher confidence.",
    )


def infer_recipient_state(
    signals: ContextSignalBundle,
    trust_profile: TrustProfile,
    interaction_history: list[dict],
    *,
    life_contexts: list[str] | None = None,  # Foundation: Phase 2 overrides
) -> RecipientState:
    """Infer the recipient's current state from available signals.

    Phase 1 inference rules:
    - Workday morning / midday / afternoon → busy, low receptivity
    - Weekend → free, high receptivity
    - Late night → sleeping, very low energy
    - Evening / night → free, winding down
    - Negative sentiment signal → stressed
    - Positive sentiment signal → positive
    - Long silence (days_since_last_reply > 3) → lonely
    - Anniversary → celebratory
    - No signals → neutral defaults

    Confidence = (distinct signal sources present) / (Phase 1 max sources).
    """
    time_of_day = _sig(signals, "time_of_day")
    day_type = _sig(signals, "day_type")
    sentiment = _sig(signals, "interaction:last_response_sentiment")
    days_since = _sig(signals, "interaction:days_since_last_reply")
    anniversary = _sig(signals, "seasonal:entity_anniversary")

    availability, energy, receptivity = _infer_situational(time_of_day, day_type)
    emotional_context = _infer_emotional(sentiment, days_since, anniversary)
    confidence = _compute_confidence(signals)

    return RecipientState(
        likely_availability=availability,
        likely_energy=energy,
        likely_receptivity=receptivity,
        emotional_context=emotional_context,
        state_confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sig(bundle: ContextSignalBundle, key: str) -> str | None:
    s = bundle.get_signal(key)
    return s.signal_value if s else None


def _infer_situational(
    time_of_day: str | None,
    day_type: str | None,
) -> tuple[str, float, float]:
    """Return (availability, likely_energy, likely_receptivity)."""
    if time_of_day == "late_night":
        return "sleeping", 0.15, 0.2

    if time_of_day == "early_morning":
        return "free", 0.3, 0.4

    if day_type == "weekend":
        return "free", 0.65, 0.75

    if time_of_day in _WORK_HOURS:
        return "busy", 0.55, 0.35

    if time_of_day == "evening":
        return "free", 0.5, 0.6

    if time_of_day == "night":
        return "free", 0.35, 0.5

    # No time signal — default to free / medium state
    return "free", 0.5, 0.5


def _infer_emotional(
    sentiment: str | None,
    days_since: str | None,
    anniversary: str | None,
) -> str:
    """Precedence: anniversary > negative sentiment > long silence > positive > neutral."""
    if anniversary == "true":
        return "celebratory"

    if sentiment == "negative":
        return "stressed"

    if days_since is not None:
        try:
            if int(days_since) > 3:
                return "lonely"
        except ValueError:
            pass

    if sentiment == "positive":
        return "positive"

    return "neutral"


def _compute_confidence(bundle: ContextSignalBundle) -> float:
    """Fraction of Phase 1 signal sources that are present."""
    if not bundle.signals:
        return 0.0
    present = {s.source for s in bundle.signals} & _PHASE1_SOURCES
    return round(len(present) / len(_PHASE1_SOURCES), 4)

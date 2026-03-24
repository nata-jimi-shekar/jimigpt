"""Message effectiveness tracking.

Records how well each message performed its intended function and
computes a normalised effectiveness score for feedback-loop learning.

Scoring (max 0.7 — reflects the three observable signals in Phase 1):
  +0.3  positive user reaction (emoji / thumbs-up)
  +0.2  user replied
  +0.2  reply sentiment was positive
   0.0  no observable response (baseline)

The 0.7 ceiling is intentional: a perfect message still has 0.3 of
unmeasured impact (lingering warmth, mood lift not expressed). Phase 2
will introduce richer signals that push the ceiling higher.
"""

from pydantic import BaseModel, Field

from src.messaging.models import MessageIntent
from src.personality.models import ToneSpectrum

# Scoring weights — must stay in sync with docstring above
_POSITIVE_REACTION_WEIGHT: float = 0.3
_REPLY_WEIGHT: float = 0.2
_POSITIVE_SENTIMENT_WEIGHT: float = 0.2


class MessageEffectiveness(BaseModel):
    """Tracks how well a single message performed its intended function."""

    message_id: str

    # What was intended
    intended_intent: MessageIntent
    intended_tone: ToneSpectrum

    # What happened
    user_reaction: str | None          # "positive" | "negative" | None
    user_replied: bool
    reply_sentiment: str | None        # "positive" | "neutral" | "negative"
    time_to_reaction_seconds: int | None

    # Derived score (set by record_effectiveness, not computed by model)
    effectiveness_score: float = Field(ge=0.0, le=1.0)


def score_effectiveness(
    user_reaction: str | None,
    user_replied: bool,
    reply_sentiment: str | None,
) -> float:
    """Compute an effectiveness score from the three observable signals.

    Returns a float in [0.0, 1.0].  Maximum achievable score is 0.7.
    """
    score = 0.0
    if user_reaction == "positive":
        score += _POSITIVE_REACTION_WEIGHT
    if user_replied:
        score += _REPLY_WEIGHT
    if reply_sentiment == "positive":
        score += _POSITIVE_SENTIMENT_WEIGHT
    return round(min(score, 1.0), 10)


def record_effectiveness(
    *,
    message_id: str,
    intended_intent: MessageIntent,
    intended_tone: ToneSpectrum,
    user_reaction: str | None,
    user_replied: bool,
    reply_sentiment: str | None,
    time_to_reaction_seconds: int | None,
) -> MessageEffectiveness:
    """Build a MessageEffectiveness record with the score computed automatically."""
    return MessageEffectiveness(
        message_id=message_id,
        intended_intent=intended_intent,
        intended_tone=intended_tone,
        user_reaction=user_reaction,
        user_replied=user_replied,
        reply_sentiment=reply_sentiment,
        time_to_reaction_seconds=time_to_reaction_seconds,
        effectiveness_score=score_effectiveness(user_reaction, user_replied, reply_sentiment),
    )

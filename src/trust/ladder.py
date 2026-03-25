"""Trust ladder models — TrustStage, TrustProfile, TrustEvent.

The trust ladder tracks the progressive relationship deepening between a user
and their entity's Digital Twin. The engine is entity-agnostic; product-specific
progression rules are injected at evaluation time.

Foundation field: TrustProfile.recipient_id prepares for Phase 2 multi-recipient
support. In Phase 1, recipient_id equals the entity owner's user_id.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TrustStage(StrEnum):
    STRANGER = "stranger"   # First 24 hours
    INITIAL = "initial"     # Days 2-7
    WORKING = "working"     # Weeks 2-4
    DEEP = "deep"           # Month 2+
    ALLIANCE = "alliance"   # Month 3+


class TrustEventType(StrEnum):
    MESSAGE_SENT = "message_sent"
    USER_REPLIED = "user_replied"
    POSITIVE_REACTION = "positive_reaction"
    NEGATIVE_REACTION = "negative_reaction"
    PERSONALITY_ADJUSTED = "personality_adjusted"
    SILENCE_PERIOD = "silence_period"


class TrustProfile(BaseModel):
    """Tracks the trust relationship between one recipient and one entity.

    Foundation field: recipient_id supports Phase 2 multi-recipient delivery.
    In Phase 1, recipient_id = owner user_id. This field must not change
    Phase 1 behaviour — it is metadata only until Phase 2 activates it.

    Note: No entity speaks without primary owner consent (B2B foundation
    principle — protects the owner's relationship with the entity).
    """

    user_id: str
    entity_id: str
    recipient_id: str  # Foundation: Phase 2 multi-recipient. Phase 1 = user_id.
    current_stage: TrustStage
    stage_entered_at: datetime

    # Interaction counters — all non-negative
    total_interactions: int = Field(default=0, ge=0)
    positive_reactions: int = Field(default=0, ge=0)
    negative_reactions: int = Field(default=0, ge=0)
    longest_silence_days: int = Field(default=0, ge=0)
    personality_adjustments: int = Field(default=0, ge=0)

    # Product-configurable progression rules injected at evaluation time
    progression_rules: dict[str, Any] = Field(default_factory=dict)


class TrustEvent(BaseModel):
    """Records a single trust-relevant interaction or signal.

    Events feed the TrustProfile counters and drive stage progression.
    """

    event_id: str
    entity_id: str
    user_id: str
    event_type: TrustEventType
    event_data: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime

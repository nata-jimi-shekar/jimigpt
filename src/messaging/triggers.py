"""Trigger rule models and enums for the message pipeline."""

from enum import StrEnum

from pydantic import BaseModel, Field


class TriggerType(StrEnum):
    TIME_BASED = "time_based"       # Fires at specific times
    EVENT_BASED = "event_based"     # Fires relative to calendar events
    RANDOM_INTERVAL = "random"      # Fires at random times within a window
    RESPONSE_TRIGGERED = "response" # Fires based on user's last response
    MILESTONE = "milestone"         # Fires at product-specific milestones


class TriggerRule(BaseModel):
    """A single rule that describes when and why a message should fire."""

    rule_id: str
    trigger_type: TriggerType
    product: str
    entity_id: str

    # Time-based fields
    schedule_cron: str | None = None  # Cron expression, e.g. "0 8 * * *"
    timezone: str = "UTC"

    # Event-based fields
    event_type: str | None = None
    offset_minutes: int = 0  # Minutes before (-) or after (+) the event

    # Random interval fields
    window_start: str | None = None  # e.g. "09:00"
    window_end: str | None = None    # e.g. "21:00"

    # Message type this trigger generates
    message_category: str  # "greeting" | "need" | "caring" | "nudge" | etc.

    enabled: bool = True

    # --- Phase 2 Foundation Fields ---

    # Which message arc template this trigger starts.
    # None in Phase 1 — arc scheduling is a Phase 2 feature.
    arc_template: str | None = None

    # Other entities belonging to the same user/household.
    # Empty in Phase 1 — used for multi-pet scheduling coordination in Phase 2.
    sibling_entity_ids: list[str] = Field(default_factory=list)

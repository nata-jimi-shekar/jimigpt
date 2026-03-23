"""INTERACTION signal collector — models engagement patterns from user replies."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.messaging.signals import ContextSignal, ContextSignalSource


class InteractionData(BaseModel):
    """Input data for the INTERACTION signal collector.

    Phase 1: last_reply_context_tags is always an empty list.
    Phase 2: populated by reply classification (keywords extracted from reply text).
    """

    last_response_sentiment: str
    days_since_last_reply: int
    reply_pattern: str  # frequent | occasional | rare | silent
    recent_reaction: str | None
    # Foundation: extracted from reply text in Phase 2
    last_reply_context_tags: list[str] = Field(default_factory=list)


def collect_interaction_signals(
    user_id: str,
    entity_id: str,
    current_time: datetime,
    interaction_data: InteractionData,
) -> list[ContextSignal]:
    """Produce INTERACTION-source signals from engagement history.

    Signals produced:
    - interaction:last_response_sentiment
    - interaction:days_since_last_reply
    - interaction:reply_pattern
    - interaction:recent_reaction
    """
    ts = current_time
    return [
        ContextSignal(
            source=ContextSignalSource.INTERACTION,
            signal_key="interaction:last_response_sentiment",
            signal_value=interaction_data.last_response_sentiment,
            timestamp=ts,
        ),
        ContextSignal(
            source=ContextSignalSource.INTERACTION,
            signal_key="interaction:days_since_last_reply",
            signal_value=str(interaction_data.days_since_last_reply),
            timestamp=ts,
        ),
        ContextSignal(
            source=ContextSignalSource.INTERACTION,
            signal_key="interaction:reply_pattern",
            signal_value=interaction_data.reply_pattern,
            timestamp=ts,
        ),
        ContextSignal(
            source=ContextSignalSource.INTERACTION,
            signal_key="interaction:recent_reaction",
            signal_value=interaction_data.recent_reaction or "",
            timestamp=ts,
        ),
    ]

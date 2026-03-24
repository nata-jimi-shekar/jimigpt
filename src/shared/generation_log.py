"""MessageGenerationLog — full telemetry for every LLM generation.

Phase 1: stored in-memory (list). Phase 2 / F05: written to DB.
Every row is a complete training example: input context → output → score.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.messaging.composer import MessageComposition
from src.messaging.quality import QualityResult

if TYPE_CHECKING:
    from src.messaging.generator import GeneratedMessage

# ---------------------------------------------------------------------------
# In-memory store (Phase 1 only)
# ---------------------------------------------------------------------------
_LOG_STORE: list[MessageGenerationLog] = []


def get_log_store() -> list[MessageGenerationLog]:
    """Return the in-memory log store (testing / Phase 1 only)."""
    return _LOG_STORE


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class MessageGenerationLog(BaseModel):
    """Full telemetry for one LLM generation. One row = one training example."""

    # Identity
    entity_id: str
    archetype_id: str
    recipient_id: str | None = None  # Phase 2: multi-recipient

    # Input
    composition_snapshot: dict  # type: ignore[type-arg]  # Full composition as JSON
    prompt_text: str
    prompt_tokens: int

    # Output
    generated_content: str
    completion_tokens: int
    model_used: str
    provider: str
    generation_latency_ms: int
    cost_usd: float

    # Quality
    quality_gate_result: dict  # type: ignore[type-arg]  # Full QualityResult as JSON
    quality_gate_passed: bool
    regeneration_count: int

    # Effectiveness — filled later when user reacts
    effectiveness_score: float | None = None
    user_reaction: str | None = None
    user_replied: bool | None = None
    reply_sentiment: str | None = None

    # Metadata
    generated_at: datetime


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def log_generation(
    *,
    composition: MessageComposition,
    generated: GeneratedMessage,
    quality: QualityResult,
    prompt_text: str,
    regeneration_count: int = 0,
    recipient_id: str | None = None,
) -> MessageGenerationLog:
    """Create a MessageGenerationLog from generation inputs and store locally.

    Phase 1: appends to in-memory list. Phase 2 / F05: writes to DB.
    """
    record = MessageGenerationLog(
        entity_id=composition.entity_voice.entity_id,
        archetype_id=composition.entity_voice.primary_archetype,
        recipient_id=recipient_id,
        composition_snapshot=composition.model_dump(mode="json"),
        prompt_text=prompt_text,
        prompt_tokens=generated.prompt_tokens,
        generated_content=generated.content,
        completion_tokens=generated.completion_tokens,
        model_used=generated.model_used,
        provider=generated.provider,
        generation_latency_ms=generated.latency_ms,
        cost_usd=generated.cost_usd,
        quality_gate_result=quality.model_dump(mode="json"),
        quality_gate_passed=quality.passed,
        regeneration_count=regeneration_count,
        generated_at=datetime.now(tz=timezone.utc),
    )
    _LOG_STORE.append(record)
    return record

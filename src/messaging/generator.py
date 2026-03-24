"""LLM message generator.

Calls the Anthropic Claude API with the composed 8-block system prompt
and returns a GeneratedMessage carrying the content and metadata needed
for the quality gate and effectiveness tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import anthropic
from pydantic import BaseModel, Field

from src.messaging.composer import MessageComposer, MessageComposition
from src.messaging.models import MessageIntent
from src.personality.models import ToneSpectrum

DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_MAX_TOKENS = 200
_GENERATE_TRIGGER = "Please generate the message now."

_composer = MessageComposer()


class GenerationError(Exception):
    """Raised when LLM generation fails in a non-retryable way."""


class GeneratedMessage(BaseModel):
    """Output of one LLM generation call."""

    message_id: str
    entity_id: str
    content: str
    generated_at: datetime
    model_used: str
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)

    # From composition — carried forward for quality gate and tracking
    message_category: str
    intended_intent: MessageIntent
    intended_tone: ToneSpectrum
    character_count: int = Field(ge=0)


async def generate_message(
    composition: MessageComposition,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    client: anthropic.AsyncAnthropic | None = None,
) -> GeneratedMessage:
    """Generate one message via the Anthropic API.

    The composed 8-block system prompt is passed as the ``system`` parameter.
    A minimal user message triggers generation.  The client can be injected
    for testing; production code leaves it None and creates a real client.
    """
    _client = client if client is not None else anthropic.AsyncAnthropic()

    prompt = _composer.to_prompt(composition)

    response = await _client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=prompt.system_prompt,
        messages=[{"role": "user", "content": _GENERATE_TRIGGER}],
    )

    if not response.content:
        raise GenerationError("API returned empty content list — no message generated.")

    content: str = response.content[0].text
    prompt_tokens: int = response.usage.input_tokens
    completion_tokens: int = response.usage.output_tokens

    return GeneratedMessage(
        message_id=str(uuid.uuid4()),
        entity_id=composition.entity_voice.entity_id,
        content=content,
        generated_at=datetime.now(tz=timezone.utc),
        model_used=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        message_category=composition.message_category,
        intended_intent=composition.intent.primary_intent,
        intended_tone=composition.tone,
        character_count=len(content),
    )

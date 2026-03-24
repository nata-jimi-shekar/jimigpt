"""LLM message generator.

Calls the configured LLM provider with the composed 8-block system prompt
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
from src.shared.llm import (
    AnthropicProvider,
    BaseProvider,
    GenerationError,
    LLMProvider,
    ModelConfig,
    RoutingDecision,
)

DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_MAX_TOKENS = 200
_GENERATE_TRIGGER = "Please generate the message now."

_composer = MessageComposer()


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

    # Provider metadata (Phase 1 defaults; populated by provider abstraction)
    provider: str = "anthropic"
    cost_usd: float = 0.0
    latency_ms: int = 0


def _default_provider(model: str) -> AnthropicProvider:
    config = ModelConfig(
        provider=LLMProvider.ANTHROPIC,
        model_id=model,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        max_tokens=_DEFAULT_MAX_TOKENS,
    )
    routing = RoutingDecision(
        selected_model=config,
        reason="primary",
        fallback_chain=[],
        routing_rule="default",
    )
    return AnthropicProvider(model_config=config, routing_decision=routing)


async def generate_message(
    composition: MessageComposition,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    client: anthropic.AsyncAnthropic | None = None,
    provider: BaseProvider | None = None,
) -> GeneratedMessage:
    """Generate one message via the configured LLM provider.

    ``provider`` takes a BaseProvider instance (preferred).
    ``client`` is kept for backward compatibility — when provided, it is
    passed through to AnthropicProvider so existing tests continue to work.
    """
    _provider = provider or _default_provider(model)
    prompt = _composer.to_prompt(composition)

    generate_kwargs: dict[str, object] = {}
    if client is not None:
        generate_kwargs["client"] = client

    llm_response = await _provider.generate(
        system_prompt=prompt.system_prompt,
        user_message=_GENERATE_TRIGGER,
        model=model,
        max_tokens=max_tokens,
        **generate_kwargs,
    )

    return GeneratedMessage(
        message_id=str(uuid.uuid4()),
        entity_id=composition.entity_voice.entity_id,
        content=llm_response.content,
        generated_at=datetime.now(tz=timezone.utc),
        model_used=model,
        prompt_tokens=llm_response.input_tokens,
        completion_tokens=llm_response.output_tokens,
        message_category=composition.message_category,
        intended_intent=composition.intent.primary_intent,
        intended_tone=composition.tone,
        character_count=len(llm_response.content),
        provider=llm_response.provider.value,
        cost_usd=llm_response.cost_usd,
        latency_ms=llm_response.latency_ms,
    )

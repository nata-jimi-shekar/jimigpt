"""LLM provider interface and response models.

Provider-agnostic abstraction layer. All LLM calls go through BaseProvider.
Concrete implementations live in the same module (AnthropicProvider, stubs).
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import anthropic
from pydantic import BaseModel

if TYPE_CHECKING:
    pass


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"    # Phase 2: Ollama/vLLM
    CACHED = "cached"  # Fallback: pre-generated messages


class ModelConfig(BaseModel):
    """Configuration for one model endpoint."""

    provider: LLMProvider
    model_id: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    supports_system_prompt: bool = True
    prompt_format: str = "standard"   # "standard" | "chatml" | "llama"
    quality_tier: str = "standard"    # "economy" | "standard" | "premium"


class RoutingDecision(BaseModel):
    """Why a specific model was chosen for this message."""

    selected_model: ModelConfig
    reason: str           # "primary" | "fallback_primary_down" | "cost_optimization" | "quality_test"
    fallback_chain: list[str]  # Models tried before this one
    routing_rule: str     # Which rule selected this model


class LLMResponse(BaseModel):
    """Normalized response from any provider."""

    content: str
    provider: LLMProvider
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float       # Computed from ModelConfig rates
    latency_ms: int
    routing_decision: RoutingDecision


class GenerationError(Exception):
    """Raised when LLM generation fails."""


class BaseProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str,
        max_tokens: int,
        client: object | None = None,
    ) -> LLMResponse: ...


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""

    _GENERATE_TRIGGER = "Please generate the message now."

    def __init__(
        self,
        model_config: ModelConfig,
        routing_decision: RoutingDecision,
    ) -> None:
        self._model_config = model_config
        self._routing_decision = routing_decision

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str,
        max_tokens: int,
        client: object | None = None,
    ) -> LLMResponse:
        _client: anthropic.AsyncAnthropic = (
            client  # type: ignore[assignment]
            if client is not None
            else anthropic.AsyncAnthropic()
        )
        start = time.monotonic()
        try:
            response = await _client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
        except Exception as exc:
            raise GenerationError(f"Anthropic API error: {exc}") from exc

        latency_ms = int((time.monotonic() - start) * 1000)

        if not response.content:
            raise GenerationError("Anthropic returned empty content.")

        content: str = response.content[0].text
        input_tokens: int = response.usage.input_tokens
        output_tokens: int = response.usage.output_tokens
        cost_usd = (
            input_tokens / 1000 * self._model_config.cost_per_1k_input
            + output_tokens / 1000 * self._model_config.cost_per_1k_output
        )

        return LLMResponse(
            content=content,
            provider=LLMProvider.ANTHROPIC,
            model_id=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            routing_decision=self._routing_decision,
        )

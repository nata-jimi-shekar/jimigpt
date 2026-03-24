"""LLM provider interface and response models.

Provider-agnostic abstraction layer. All LLM calls go through BaseProvider.
Concrete implementations live in the same module (AnthropicProvider, stubs).
"""

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel


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
    ) -> LLMResponse: ...

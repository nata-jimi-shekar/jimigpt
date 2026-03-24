"""LLM routing config and provider factory.

Loads config/llm_routing.yaml and returns the correct BaseProvider for a
given routing rule. In Phase 1, all Anthropic-primary rules return
AnthropicProvider. OpenAI/Local stubs raise NotConfiguredError if selected.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from src.shared.llm import (
    MODEL_COSTS,
    AnthropicProvider,
    BaseProvider,
    LLMProvider,
    ModelConfig,
    RoutingDecision,
    _DEFAULT_INPUT_COST,
    _DEFAULT_OUTPUT_COST,
)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "llm_routing.yaml"


class RoutingConfig(BaseModel):
    """One routing rule from llm_routing.yaml."""

    primary: str
    fallback: list[str] = []
    max_cost_per_message_usd: float = 0.001


def load_routing_config() -> dict[str, Any]:
    """Load and return the raw routing config dict from YAML."""
    with _CONFIG_PATH.open() as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def _parse_provider_string(provider_str: str) -> tuple[str, str]:
    """Parse 'provider:model_id' into (provider, model_id)."""
    provider, _, model_id = provider_str.partition(":")
    return provider, model_id


def _make_anthropic_provider(model_id: str, routing_rule: str) -> AnthropicProvider:
    input_cost, output_cost = MODEL_COSTS.get(
        model_id, (_DEFAULT_INPUT_COST, _DEFAULT_OUTPUT_COST)
    )
    config = ModelConfig(
        provider=LLMProvider.ANTHROPIC,
        model_id=model_id,
        cost_per_1k_input=input_cost,
        cost_per_1k_output=output_cost,
        max_tokens=200,
    )
    decision = RoutingDecision(
        selected_model=config,
        reason="primary",
        fallback_chain=[],
        routing_rule=routing_rule,
    )
    return AnthropicProvider(model_config=config, routing_decision=decision)


def get_provider(config_key: str) -> BaseProvider:
    """Return the appropriate BaseProvider for the given routing rule.

    Unknown keys fall back to the 'default' rule. In Phase 1, all
    Anthropic-primary rules return AnthropicProvider.
    """
    raw = load_routing_config()
    rule_data = raw.get(config_key) or raw["default"]

    primary: str = rule_data.get("primary", "anthropic:claude-haiku-4-5")
    provider_name, model_id = _parse_provider_string(primary)

    if provider_name == LLMProvider.ANTHROPIC:
        return _make_anthropic_provider(model_id, config_key)

    # Non-Anthropic primaries fall back to default Anthropic in Phase 1
    default_primary: str = raw["default"]["primary"]
    _, default_model_id = _parse_provider_string(default_primary)
    return _make_anthropic_provider(default_model_id, "default")

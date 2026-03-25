"""Tests for LLM routing config and provider factory."""

from __future__ import annotations

import pytest

from src.shared.llm import AnthropicProvider
from src.shared.routing import (
    InvalidRoutingConfig,
    RoutingConfig,
    get_provider,
    load_routing_config,
    _parse_provider_string,
)


class TestLoadRoutingConfig:
    def test_loads_without_error(self) -> None:
        config = load_routing_config()
        assert config is not None

    def test_has_default_rule(self) -> None:
        config = load_routing_config()
        assert "default" in config

    def test_has_high_stakes_rule(self) -> None:
        config = load_routing_config()
        assert "high_stakes" in config

    def test_has_quality_test_rule(self) -> None:
        config = load_routing_config()
        assert "quality_test" in config

    def test_default_primary_is_anthropic_haiku(self) -> None:
        config = load_routing_config()
        assert config["default"]["primary"] == "anthropic:claude-haiku-4-5"

    def test_high_stakes_primary_is_anthropic_sonnet(self) -> None:
        config = load_routing_config()
        assert config["high_stakes"]["primary"] == "anthropic:claude-sonnet-4-6"


class TestRoutingConfig:
    def test_validates_correctly(self) -> None:
        rc = RoutingConfig(
            primary="anthropic:claude-haiku-4-5",
            fallback=["cached:personality_matched"],
            max_cost_per_message_usd=0.001,
        )
        assert rc.primary == "anthropic:claude-haiku-4-5"
        assert len(rc.fallback) == 1

    def test_fallback_defaults_to_empty(self) -> None:
        rc = RoutingConfig(primary="anthropic:claude-haiku-4-5")
        assert rc.fallback == []


class TestGetProvider:
    def test_default_returns_anthropic_provider(self) -> None:
        provider = get_provider("default")
        assert isinstance(provider, AnthropicProvider)

    def test_high_stakes_returns_anthropic_provider(self) -> None:
        # Both are Anthropic in Phase 1 — OpenAI/Local not configured
        provider = get_provider("high_stakes")
        assert isinstance(provider, AnthropicProvider)

    def test_first_impression_returns_anthropic_provider(self) -> None:
        provider = get_provider("first_impression")
        assert isinstance(provider, AnthropicProvider)

    def test_unknown_key_falls_back_to_default(self) -> None:
        provider = get_provider("nonexistent_rule")
        assert isinstance(provider, AnthropicProvider)

    def test_default_model_id_is_haiku(self) -> None:
        provider = get_provider("default")
        assert isinstance(provider, AnthropicProvider)
        assert "haiku" in provider.model_id

    def test_high_stakes_model_id_is_sonnet(self) -> None:
        provider = get_provider("high_stakes")
        assert isinstance(provider, AnthropicProvider)
        assert "sonnet" in provider.model_id


# ---------------------------------------------------------------------------
# Issue #1: Malformed provider strings must be validated
# ---------------------------------------------------------------------------


class TestParseProviderStringValidation:
    def test_valid_string_parses(self) -> None:
        provider, model_id = _parse_provider_string("anthropic:claude-haiku-4-5")
        assert provider == "anthropic"
        assert model_id == "claude-haiku-4-5"

    def test_missing_colon_raises(self) -> None:
        with pytest.raises(InvalidRoutingConfig):
            _parse_provider_string("anthropic")

    def test_empty_model_id_raises(self) -> None:
        with pytest.raises(InvalidRoutingConfig):
            _parse_provider_string("anthropic:")

    def test_empty_provider_raises(self) -> None:
        with pytest.raises(InvalidRoutingConfig):
            _parse_provider_string(":claude-haiku-4-5")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidRoutingConfig):
            _parse_provider_string("")

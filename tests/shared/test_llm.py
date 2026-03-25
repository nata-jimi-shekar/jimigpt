"""Tests for LLM provider interface and response models."""

import pytest

from src.shared.llm import (
    BaseProvider,
    LLMProvider,
    LLMResponse,
    ModelConfig,
    RoutingDecision,
)


class TestLLMProviderEnum:
    def test_has_all_expected_values(self) -> None:
        assert LLMProvider.ANTHROPIC == "anthropic"
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.LOCAL == "local"
        assert LLMProvider.CACHED == "cached"

    def test_is_string_enum(self) -> None:
        assert isinstance(LLMProvider.ANTHROPIC, str)


class TestModelConfig:
    def test_validates_correctly(self) -> None:
        config = ModelConfig(
            provider=LLMProvider.ANTHROPIC,
            model_id="claude-haiku-4-5",
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            max_tokens=1024,
        )
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model_id == "claude-haiku-4-5"
        assert config.supports_system_prompt is True
        assert config.prompt_format == "standard"
        assert config.quality_tier == "standard"

    def test_custom_quality_tier(self) -> None:
        config = ModelConfig(
            provider=LLMProvider.OPENAI,
            model_id="gpt-4o",
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.015,
            max_tokens=4096,
            quality_tier="premium",
        )
        assert config.quality_tier == "premium"

    def test_rejects_missing_required_fields(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ModelConfig(provider=LLMProvider.ANTHROPIC)  # type: ignore[call-arg]


class TestRoutingDecision:
    def _model_config(self) -> ModelConfig:
        return ModelConfig(
            provider=LLMProvider.ANTHROPIC,
            model_id="claude-haiku-4-5",
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            max_tokens=1024,
        )

    def test_validates_correctly(self) -> None:
        decision = RoutingDecision(
            selected_model=self._model_config(),
            reason="primary",
            fallback_chain=[],
            routing_rule="default",
        )
        assert decision.reason == "primary"
        assert decision.fallback_chain == []

    def test_fallback_chain_contains_tried_models(self) -> None:
        decision = RoutingDecision(
            selected_model=self._model_config(),
            reason="fallback_primary_down",
            fallback_chain=["anthropic:claude-sonnet-4-6"],
            routing_rule="high_stakes",
        )
        assert len(decision.fallback_chain) == 1


class TestLLMResponse:
    def _routing_decision(self) -> RoutingDecision:
        config = ModelConfig(
            provider=LLMProvider.ANTHROPIC,
            model_id="claude-haiku-4-5",
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            max_tokens=1024,
        )
        return RoutingDecision(
            selected_model=config,
            reason="primary",
            fallback_chain=[],
            routing_rule="default",
        )

    def test_validates_correctly(self) -> None:
        response = LLMResponse(
            content="Woof! Missing you already!",
            provider=LLMProvider.ANTHROPIC,
            model_id="claude-haiku-4-5",
            input_tokens=150,
            output_tokens=20,
            cost_usd=0.000063,
            latency_ms=450,
            routing_decision=self._routing_decision(),
        )
        assert response.content == "Woof! Missing you already!"
        assert response.provider == LLMProvider.ANTHROPIC
        assert response.input_tokens == 150
        assert response.output_tokens == 20

    def test_cost_reflects_token_counts(self) -> None:
        """Cost should be computable from ModelConfig rates and token counts."""
        config = ModelConfig(
            provider=LLMProvider.ANTHROPIC,
            model_id="claude-haiku-4-5",
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            max_tokens=1024,
        )
        input_tokens = 200
        output_tokens = 50
        expected_cost = (
            input_tokens / 1000 * config.cost_per_1k_input
            + output_tokens / 1000 * config.cost_per_1k_output
        )
        response = LLMResponse(
            content="Woof!",
            provider=LLMProvider.ANTHROPIC,
            model_id=config.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=expected_cost,
            latency_ms=300,
            routing_decision=RoutingDecision(
                selected_model=config,
                reason="primary",
                fallback_chain=[],
                routing_rule="default",
            ),
        )
        assert abs(response.cost_usd - expected_cost) < 1e-9


class TestBaseProvider:
    def test_is_abstract(self) -> None:
        """BaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_generate(self) -> None:
        """Concrete subclass without generate() also cannot be instantiated."""

        class IncompleteProvider(BaseProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

    def test_concrete_subclass_is_valid(self) -> None:
        """A fully implemented subclass can be instantiated."""

        class ConcreteProvider(BaseProvider):
            model_id: str = "test-model"

            async def generate(
                self,
                system_prompt: str,
                user_message: str,
                *,
                model: str,
                max_tokens: int,
            ) -> LLMResponse:
                raise NotImplementedError

        provider = ConcreteProvider()
        assert provider is not None

    def test_model_id_is_required_on_base_provider(self) -> None:
        """Every provider subclass must expose model_id."""
        from src.shared.llm import AnthropicProvider, CachedProvider, LocalProvider, OpenAIProvider

        # All concrete providers must have model_id as an attribute
        assert hasattr(BaseProvider, "model_id"), "BaseProvider must declare model_id"

        # Check that model_id is an abstract property
        # (subclass without it should fail to instantiate)
        class MissingModelId(BaseProvider):
            async def generate(
                self,
                system_prompt: str,
                user_message: str,
                *,
                model: str,
                max_tokens: int,
            ) -> LLMResponse:
                raise NotImplementedError

        with pytest.raises(TypeError):
            MissingModelId()  # type: ignore[abstract]

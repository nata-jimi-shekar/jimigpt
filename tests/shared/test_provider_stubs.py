"""Tests for OpenAI, Local, and Cached provider stubs."""

from __future__ import annotations

import pytest

from src.shared.llm import (
    CachedProvider,
    LLMProvider,
    LocalProvider,
    ModelConfig,
    NotConfiguredError,
    OpenAIProvider,
    RoutingDecision,
)


def _routing(provider: LLMProvider = LLMProvider.OPENAI, model_id: str = "gpt-4o-mini") -> RoutingDecision:
    return RoutingDecision(
        selected_model=ModelConfig(
            provider=provider,
            model_id=model_id,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            max_tokens=200,
        ),
        reason="primary",
        fallback_chain=[],
        routing_rule="default",
    )


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_raises_not_configured_error(self) -> None:
        provider = OpenAIProvider(routing_decision=_routing())
        with pytest.raises(NotConfiguredError):
            await provider.generate(
                "system", "user", model="gpt-4o-mini", max_tokens=200
            )

    @pytest.mark.asyncio
    async def test_error_message_is_helpful(self) -> None:
        provider = OpenAIProvider(routing_decision=_routing())
        with pytest.raises(NotConfiguredError, match="OpenAI"):
            await provider.generate(
                "system", "user", model="gpt-4o-mini", max_tokens=200
            )

    def test_is_base_provider_subclass(self) -> None:
        from src.shared.llm import BaseProvider
        assert issubclass(OpenAIProvider, BaseProvider)


class TestLocalProvider:
    @pytest.mark.asyncio
    async def test_raises_not_configured_error(self) -> None:
        provider = LocalProvider(routing_decision=_routing(LLMProvider.LOCAL, "mistral-7b"))
        with pytest.raises(NotConfiguredError):
            await provider.generate(
                "system", "user", model="mistral-7b", max_tokens=200
            )

    @pytest.mark.asyncio
    async def test_error_message_mentions_local(self) -> None:
        provider = LocalProvider(routing_decision=_routing(LLMProvider.LOCAL, "mistral-7b"))
        with pytest.raises(NotConfiguredError, match="[Ll]ocal"):
            await provider.generate(
                "system", "user", model="mistral-7b", max_tokens=200
            )

    def test_is_base_provider_subclass(self) -> None:
        from src.shared.llm import BaseProvider
        assert issubclass(LocalProvider, BaseProvider)


class TestCachedProvider:
    def _provider(self, pool: list[str] | None = None) -> CachedProvider:
        return CachedProvider(
            routing_decision=_routing(LLMProvider.CACHED, "cached"),
            message_pool=pool or [],
        )

    @pytest.mark.asyncio
    async def test_empty_pool_returns_fallback_message(self) -> None:
        provider = self._provider(pool=[])
        result = await provider.generate(
            "system", "user", model="cached", max_tokens=200
        )
        assert "unavailable" in result.content.lower()

    @pytest.mark.asyncio
    async def test_returns_llm_response(self) -> None:
        from src.shared.llm import LLMResponse
        provider = self._provider(pool=[])
        result = await provider.generate(
            "system", "user", model="cached", max_tokens=200
        )
        assert isinstance(result, LLMResponse)

    @pytest.mark.asyncio
    async def test_response_provider_is_cached(self) -> None:
        provider = self._provider(pool=[])
        result = await provider.generate(
            "system", "user", model="cached", max_tokens=200
        )
        assert result.provider == LLMProvider.CACHED

    @pytest.mark.asyncio
    async def test_non_empty_pool_returns_first_message(self) -> None:
        provider = self._provider(pool=["Hey there!", "Woof!"])
        result = await provider.generate(
            "system", "user", model="cached", max_tokens=200
        )
        assert result.content == "Hey there!"

    @pytest.mark.asyncio
    async def test_zero_tokens_and_zero_cost(self) -> None:
        provider = self._provider(pool=[])
        result = await provider.generate(
            "system", "user", model="cached", max_tokens=200
        )
        assert result.input_tokens == 0
        assert result.output_tokens == 0
        assert result.cost_usd == 0.0

    def test_is_base_provider_subclass(self) -> None:
        from src.shared.llm import BaseProvider
        assert issubclass(CachedProvider, BaseProvider)

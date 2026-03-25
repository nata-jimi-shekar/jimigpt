"""Tests for AnthropicProvider implementation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.llm import (
    AnthropicProvider,
    LLMProvider,
    LLMResponse,
    ModelConfig,
    RoutingDecision,
)


def _make_routing_decision(model_id: str = "claude-haiku-4-5") -> RoutingDecision:
    return RoutingDecision(
        selected_model=ModelConfig(
            provider=LLMProvider.ANTHROPIC,
            model_id=model_id,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            max_tokens=1024,
        ),
        reason="primary",
        fallback_chain=[],
        routing_rule="default",
    )


def _make_mock_anthropic_response(
    text: str = "Woof! Miss you!", input_tokens: int = 150, output_tokens: int = 20
) -> MagicMock:
    """Build a mock that mimics anthropic.types.Message."""
    content_block = MagicMock()
    content_block.text = text

    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens

    response = MagicMock()
    response.content = [content_block]
    response.usage = usage
    return response


class TestAnthropicProvider:
    def _provider(self) -> AnthropicProvider:
        routing = _make_routing_decision()
        return AnthropicProvider(
            model_config=routing.selected_model,
            routing_decision=routing,
        )

    @pytest.mark.asyncio
    async def test_returns_llm_response(self) -> None:
        mock_response = _make_mock_anthropic_response()
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = self._provider()

        with patch("src.shared.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            result = await provider.generate(
                system_prompt="You are Jimi.",
                user_message="Please generate the message now.",
                model="claude-haiku-4-5",
                max_tokens=200,
            )

        assert isinstance(result, LLMResponse)
        assert result.content == "Woof! Miss you!"
        assert result.provider == LLMProvider.ANTHROPIC
        assert result.model_id == "claude-haiku-4-5"

    @pytest.mark.asyncio
    async def test_populates_token_counts(self) -> None:
        mock_response = _make_mock_anthropic_response(input_tokens=200, output_tokens=35)
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = self._provider()

        with patch("src.shared.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            result = await provider.generate(
                system_prompt="You are Jimi.",
                user_message="Generate now.",
                model="claude-haiku-4-5",
                max_tokens=200,
            )

        assert result.input_tokens == 200
        assert result.output_tokens == 35

    @pytest.mark.asyncio
    async def test_cost_calculated_from_model_config_rates(self) -> None:
        input_tokens = 200
        output_tokens = 40
        mock_response = _make_mock_anthropic_response(
            input_tokens=input_tokens, output_tokens=output_tokens
        )
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        routing = _make_routing_decision()
        config = routing.selected_model
        expected_cost = (
            input_tokens / 1000 * config.cost_per_1k_input
            + output_tokens / 1000 * config.cost_per_1k_output
        )

        provider = AnthropicProvider(model_config=config, routing_decision=routing)

        with patch("src.shared.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            result = await provider.generate(
                system_prompt="You are Jimi.",
                user_message="Generate now.",
                model="claude-haiku-4-5",
                max_tokens=200,
            )

        assert abs(result.cost_usd - expected_cost) < 1e-9

    @pytest.mark.asyncio
    async def test_latency_is_positive(self) -> None:
        mock_response = _make_mock_anthropic_response()
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = self._provider()

        with patch("src.shared.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            result = await provider.generate(
                system_prompt="You are Jimi.",
                user_message="Generate now.",
                model="claude-haiku-4-5",
                max_tokens=200,
            )

        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_api_error_raises_generation_error(self) -> None:
        from src.shared.llm import GenerationError

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=Exception("API unavailable"))

        provider = self._provider()

        with patch("src.shared.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            with pytest.raises(GenerationError):
                await provider.generate(
                    system_prompt="You are Jimi.",
                    user_message="Generate now.",
                    model="claude-haiku-4-5",
                    max_tokens=200,
                )

    @pytest.mark.asyncio
    async def test_accepts_injected_client(self) -> None:
        """Client can be injected directly — used in tests."""
        mock_response = _make_mock_anthropic_response(text="Hello!")
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = self._provider()
        result = await provider.generate(
            system_prompt="You are Jimi.",
            user_message="Generate now.",
            model="claude-haiku-4-5",
            max_tokens=200,
            client=mock_client,
        )

        assert result.content == "Hello!"

    @pytest.mark.asyncio
    async def test_empty_response_raises_generation_error(self) -> None:
        """Empty content list from Anthropic should raise GenerationError."""
        from src.shared.llm import GenerationError

        mock_response = MagicMock()
        mock_response.content = []
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 0
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = self._provider()
        with pytest.raises(GenerationError):
            await provider.generate(
                system_prompt="You are Jimi.",
                user_message="Generate now.",
                model="claude-haiku-4-5",
                max_tokens=200,
                client=mock_client,
            )

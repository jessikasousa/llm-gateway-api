"""Unit tests for LLMService primary/fallback routing."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.base_llm_client import LLMResponse
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_generate_returns_primary_when_primary_succeeds() -> None:
    """Primary client result is returned and fallback is never called."""
    primary = AsyncMock()
    primary.complete = AsyncMock(
        return_value=LLMResponse(
            content="from-primary",
            model="primary-model",
            tokens_used=1,
            latency_ms=10,
        )
    )
    fallback = AsyncMock()
    fallback.complete = AsyncMock()

    service = LLMService(primary, fallback)
    result = await service.generate("prompt text without web keywords", "user-1")

    assert result.content == "from-primary"
    assert result.model == "primary-model"
    primary.complete.assert_awaited_once_with(
        "prompt text without web keywords",
        "user-1",
        grounding_enabled=False,
    )
    fallback.complete.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.llm_service.get_settings")
async def test_generate_uses_fallback_when_primary_raises(
    mock_get_settings: MagicMock,
) -> None:
    """After retries are exhausted, fallback is used with grounding."""
    mock_get_settings.return_value = MagicMock(llm_max_retries=1)

    primary = AsyncMock()
    primary.complete = AsyncMock(side_effect=ConnectionError("upstream down"))

    fallback = AsyncMock()
    fallback.complete = AsyncMock(
        return_value=LLMResponse(
            content="from-fallback",
            model="fallback-model",
            tokens_used=2,
            latency_ms=20,
        )
    )

    service = LLMService(primary, fallback)
    result = await service.generate("plain prompt", "user-2")

    assert result.content == "from-fallback"
    assert result.model == "fallback-model"
    primary.complete.assert_awaited_once_with("plain prompt", "user-2", grounding_enabled=False)
    fallback.complete.assert_awaited_once_with("plain prompt", "user-2", grounding_enabled=True)


@pytest.mark.asyncio
@patch("app.services.llm_service.get_settings")
async def test_generate_propagates_when_fallback_also_fails(
    mock_get_settings: MagicMock,
) -> None:
    """If fallback raises, that exception propagates to the caller."""
    mock_get_settings.return_value = MagicMock(llm_max_retries=1)

    primary = AsyncMock()
    primary.complete = AsyncMock(side_effect=RuntimeError("primary failed"))

    fallback = AsyncMock()
    fallback.complete = AsyncMock(side_effect=RuntimeError("fallback failed"))

    service = LLMService(primary, fallback)

    with pytest.raises(RuntimeError, match="fallback failed"):
        await service.generate("p", "user-3")

    primary.complete.assert_awaited_once()
    fallback.complete.assert_awaited_once_with("p", "user-3", grounding_enabled=True)


@pytest.mark.asyncio
async def test_generate_routes_to_gemini_when_keywords_match() -> None:
    """Prompts suggesting fresh web data skip primary and use Gemini with grounding."""
    primary = AsyncMock()
    fallback = AsyncMock()
    fallback.complete = AsyncMock(
        return_value=LLMResponse(
            content="grounded",
            model="gemini",
            tokens_used=1,
            latency_ms=1,
        )
    )

    service = LLMService(primary, fallback)
    result = await service.generate("Como esta a cotacao do dolar hoje?", "u1")

    assert result.content == "grounded"
    primary.complete.assert_not_called()
    fallback.complete.assert_awaited_once_with(
        "Como esta a cotacao do dolar hoje?",
        "u1",
        grounding_enabled=True,
    )


@pytest.mark.asyncio
async def test_generate_routes_to_gemini_when_use_web_search_true() -> None:
    """Explicit use_web_search forces Gemini with grounding."""
    primary = AsyncMock()
    fallback = AsyncMock()
    fallback.complete = AsyncMock(
        return_value=LLMResponse(
            content="x",
            model="gemini",
            tokens_used=1,
            latency_ms=1,
        )
    )

    service = LLMService(primary, fallback)
    await service.generate("relativity theory", "u1", use_web_search=True)

    primary.complete.assert_not_called()
    fallback.complete.assert_awaited_once_with(
        "relativity theory",
        "u1",
        grounding_enabled=True,
    )


def test_requires_web_search_accent_insensitive() -> None:
    """Keywords match after removing accents."""
    assert LLMService._requires_web_search("Cotação do dólar")
    assert not LLMService._requires_web_search("Explain tensors")

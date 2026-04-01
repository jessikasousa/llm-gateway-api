"""Unit tests for LLMService primary/fallback routing."""
from unittest.mock import AsyncMock

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
    result = await service.generate("prompt text", "user-1")

    assert result.content == "from-primary"
    assert result.model == "primary-model"
    primary.complete.assert_awaited_once_with("prompt text", "user-1")
    fallback.complete.assert_not_called()


@pytest.mark.asyncio
async def test_generate_uses_fallback_when_primary_raises() -> None:
    """Any exception from primary triggers fallback; fallback result is returned."""
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
    result = await service.generate("p", "user-2")

    assert result.content == "from-fallback"
    assert result.model == "fallback-model"
    primary.complete.assert_awaited_once()
    fallback.complete.assert_awaited_once_with("p", "user-2")


@pytest.mark.asyncio
async def test_generate_propagates_when_fallback_also_fails() -> None:
    """If fallback raises, that exception propagates to the caller."""
    primary = AsyncMock()
    primary.complete = AsyncMock(side_effect=RuntimeError("primary failed"))

    fallback = AsyncMock()
    fallback.complete = AsyncMock(side_effect=RuntimeError("fallback failed"))

    service = LLMService(primary, fallback)

    with pytest.raises(RuntimeError, match="fallback failed"):
        await service.generate("p", "user-3")

    primary.complete.assert_awaited_once()
    fallback.complete.assert_awaited_once()

"""LLM client unit tests with mocked HTTP calls."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.clients.openrouter_client import OpenRouterClient
from app.clients.gemini_client import GeminiClient
from app.clients.base_llm_client import LLMResponse


# ── OpenRouter ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_openrouter_returns_llm_response():
    """OpenRouterClient.complete should return a valid LLMResponse."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello from OpenRouter!"}}],
        "model": "openai/gpt-3.5-turbo",
        "usage": {"total_tokens": 42},
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.clients.openrouter_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        client = OpenRouterClient()
        result = await client.complete("Test prompt", user_id="user-1")

    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from OpenRouter!"
    assert result.tokens_used == 42
    assert result.latency_ms is not None


@pytest.mark.asyncio
async def test_openrouter_raises_on_http_error():
    """OpenRouterClient should propagate HTTP errors."""
    import httpx

    with patch("app.clients.openrouter_client.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=MagicMock()
        )
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        client = OpenRouterClient()

        with pytest.raises(httpx.HTTPStatusError):
            await client.complete("Test prompt", user_id="user-1")


# ── Gemini ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gemini_returns_llm_response():
    """GeminiClient.complete should return a valid LLMResponse."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": "Hello from Gemini!"}]}}
        ],
        "usageMetadata": {"totalTokenCount": 10},
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.clients.gemini_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        client = GeminiClient()
        result = await client.complete("Test prompt", user_id="user-1")

    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from Gemini!"
    assert result.tokens_used == 10
    assert result.latency_ms is not None
"""Google Gemini LLM provider client."""
import time

import httpx

from app.clients.base_llm_client import BaseLLMClient, LLMResponse
from app.config.settings import get_settings


class GeminiClient(BaseLLMClient):
    """Async HTTP client for Google Gemini API."""

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self._timeout = settings.llm_timeout_seconds

    async def complete(self, prompt: str, user_id: str) -> LLMResponse:
        """Send prompt to Gemini and return standardized response."""
        url = f"{self._BASE_URL}/{self._model}:generateContent"

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        start = time.monotonic()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                url,
                json=payload,
                params={"key": self._api_key},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)
        data = response.json()

        content = (
            data["candidates"][0]["content"]["parts"][0]["text"]
        )
        tokens_used = data.get("usageMetadata", {}).get("totalTokenCount")

        return LLMResponse(
            content=content,
            model=self._model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
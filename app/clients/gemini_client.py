"""Google Gemini LLM provider client."""
import time
import logging

import httpx

from app.clients.base_llm_client import BaseLLMClient, LLMResponse
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Async HTTP client for Google Gemini API.

    Uses the official REST API as documented in the quickstart:
    POST .../models/{model}:generateContent with the x-goog-api-key header.
    """

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
                    "parts": [{"text": prompt}],
                },
            ],
        }

        start = time.monotonic()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            logger.debug(
                "Sending request to Gemini",
                extra={
                    "user_id": user_id,
                    "model": self._model,
                    "url": url,
                    "payload": payload,
                },
            )
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self._api_key,
                },
            )
            response.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)
        data = response.json()

        content = (
            data["candidates"][0]["content"]["parts"][0]["text"]
        )
        tokens_used = data.get("usageMetadata", {}).get("totalTokenCount")

        logger.debug(
            "Received response from Gemini",
            extra={
                "user_id": user_id,
                "model": self._model,
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
            },
        )

        return LLMResponse(
            content=content,
            model=self._model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
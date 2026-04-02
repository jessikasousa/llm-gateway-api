"""Google Gemini LLM provider client."""
import time
import logging

import httpx

from app.clients.base_llm_client import BaseLLMClient, LLMResponse
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def _extract_candidate_text(data: dict) -> str:
    """Concatenate text parts from the first candidate (grounding may use multiple parts)."""
    parts = data["candidates"][0]["content"].get("parts") or []
    return "".join(p.get("text", "") for p in parts if isinstance(p, dict))


class GeminiClient(BaseLLMClient):
    """Async HTTP client for Google Gemini API.

    Uses the official REST API as documented in the quickstart:
    POST .../models/{model}:generateContent with the x-goog-api-key header.

    Grounding uses the ``google_search`` tool per REST docs (Gemini 2+). Older
    models may require ``google_search_retrieval`` instead; see Google AI docs.
    """

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self._timeout = settings.llm_timeout_seconds

    async def complete(
        self,
        prompt: str,
        user_id: str,
        *,
        grounding_enabled: bool = False,
    ) -> LLMResponse:
        """Send prompt to Gemini and return standardized response.

        When ``grounding_enabled`` is True, enables Grounding with Google Search
        via the ``google_search`` tool in the request body.
        """
        url = f"{self._BASE_URL}/{self._model}:generateContent"

        payload: dict = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                },
            ],
        }
        if grounding_enabled:
            payload["tools"] = [{"google_search": {}}]

        start = time.monotonic()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            logger.debug(
                "Sending request to Gemini",
                extra={
                    "user_id": user_id,
                    "model": self._model,
                    "url": url,
                    "grounding_enabled": grounding_enabled,
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

        content = _extract_candidate_text(data)
        tokens_used = data.get("usageMetadata", {}).get("totalTokenCount")

        logger.debug(
            "Received response from Gemini",
            extra={
                "user_id": user_id,
                "model": self._model,
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
                "grounding_enabled": grounding_enabled,
            },
        )

        return LLMResponse(
            content=content,
            model=self._model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

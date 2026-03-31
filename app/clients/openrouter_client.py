"""OpenRouter LLM provider client."""
import time

import httpx

from app.clients.base_llm_client import BaseLLMClient, LLMResponse
from app.config.settings import get_settings


class OpenRouterClient(BaseLLMClient):
    """Async HTTP client for OpenRouter API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._base_url = settings.openrouter_base_url
        self._model = settings.openrouter_model
        self._timeout = settings.llm_timeout_seconds

    async def complete(self, prompt: str, user_id: str) -> LLMResponse:
        """Send prompt to OpenRouter and return standardized response."""
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-Title": "llm-gateway-api",
        }

        start = time.monotonic()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens")
        model_used = data.get("model", self._model)

        return LLMResponse(
            content=content,
            model=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
import logging

from app.clients.base_llm_client import BaseLLMClient, LLMResponse

_log = logging.getLogger(__name__)


class LLMService:
    """Route generation to a primary LLM client with fallback on any failure."""

    def __init__(self, primary_client: BaseLLMClient, fallback_client: BaseLLMClient) -> None:
        self._primary_client: BaseLLMClient = primary_client
        self._fallback_client: BaseLLMClient = fallback_client

    async def generate(self, prompt: str, user_id: str) -> LLMResponse:
        """Try the primary provider; on any exception, log and use the fallback."""
        try:
            return await self._primary_client.complete(prompt, user_id)
        except Exception as exc:
            _log.warning(
                "Primary LLM provider failed; attempting fallback",
                extra={"error": str(exc), "user_id": user_id},
            )
            return await self._fallback_client.complete(prompt, user_id)

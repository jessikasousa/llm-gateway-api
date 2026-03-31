from app.clients.base_llm_client import BaseLLMClient, LLMResponse


class LLMService:
    """Service stub that will manage provider routing and fallback."""

    def __init__(self, primary_client: BaseLLMClient, fallback_client: BaseLLMClient) -> None:
        self._primary_client: BaseLLMClient = primary_client
        self._fallback_client: BaseLLMClient = fallback_client

    async def generate(self, prompt: str, user_id: str) -> LLMResponse:
        """Generate completion using configured provider strategy."""
        raise NotImplementedError("LLM routing logic will be implemented later.")

from app.clients.base_llm_client import BaseLLMClient, LLMResponse


class OpenRouterClient(BaseLLMClient):
    """Client stub that will call OpenRouter asynchronously."""

    async def complete(self, prompt: str, user_id: str) -> LLMResponse:
        """Generate completion from OpenRouter provider."""
        raise NotImplementedError("OpenRouter integration will be implemented later.")

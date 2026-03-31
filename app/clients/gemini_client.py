from app.clients.base_llm_client import BaseLLMClient, LLMResponse


class GeminiClient(BaseLLMClient):
    """Client stub that will call Gemini asynchronously."""

    async def complete(self, prompt: str, user_id: str) -> LLMResponse:
        """Generate completion from Gemini provider."""
        raise NotImplementedError("Gemini integration will be implemented later.")

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class LLMResponse:
    """Standardized response returned by LLM provider clients."""

    content: str
    model: str
    tokens_used: int | None
    latency_ms: int | None


class BaseLLMClient(ABC):
    """Contract for asynchronous LLM provider clients."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        user_id: str,
        *,
        grounding_enabled: bool = False,
    ) -> "LLMResponse":
        """Generate a completion for a user prompt.

        ``grounding_enabled`` is honored by providers that support web grounding
        (e.g. Gemini); others may ignore it.
        """
        raise NotImplementedError

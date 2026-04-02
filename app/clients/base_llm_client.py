from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class LLMResponse:
    """Standardized response returned by LLM provider clients."""

    content: str
    model: str
    tokens_used: int | None
    latency_ms: int | None
    response_id: str | None = None  # Adicionado para paridade com o log do service


class BaseLLMClient(ABC):
    """Contract for asynchronous LLM provider clients."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique identifier for the provider (e.g., 'gemini', 'openrouter')."""
        pass

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        user_id: str,
        *,
        grounding_enabled: bool = False,
    ) -> "LLMResponse":
        """Generate a completion for a user prompt."""
        pass

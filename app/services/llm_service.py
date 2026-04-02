"""LLM routing: hybrid web-grounding path, primary OpenRouter with retries, Gemini fallback."""
import logging
import unicodedata

from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.before_sleep import before_sleep_log

from app.clients.base_llm_client import BaseLLMClient, LLMResponse
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# Normalized (lowercase, no accents) substrings that suggest fresh web data is needed.
_WEB_SEARCH_KEYWORDS: frozenset[str] = frozenset(
    {
        "hoje",
        "agora",
        "cotacao",
        "preco",
        "noticias",
        "clima",
        "ultimas",
        "atual",
        "dolar",
        "euro",
    }
)


def _normalize_prompt_for_keywords(prompt: str) -> str:
    """Lowercase and strip accents for keyword matching."""
    lowered = prompt.lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


class LLMService:
    """Route generation: Gemini+grounding when web data is needed; else OpenRouter with retries."""

    def __init__(self, primary_client: BaseLLMClient, fallback_client: BaseLLMClient) -> None:
        self._primary_client: BaseLLMClient = primary_client
        self._fallback_client: BaseLLMClient = fallback_client

    @staticmethod
    def _requires_web_search(prompt: str) -> bool:
        """Return True if heuristics suggest the user needs up-to-date web information."""
        normalized = _normalize_prompt_for_keywords(prompt)
        return any(k in normalized for k in _WEB_SEARCH_KEYWORDS)

    async def generate(
        self,
        prompt: str,
        user_id: str,
        *,
        use_web_search: bool = False,
    ) -> LLMResponse:
        """Complete the prompt using hybrid routing and resilient fallback.

        When ``use_web_search`` is true or the prompt matches web-intent keywords,
        calls the fallback client (Gemini) with Google Search grounding immediately.

        Otherwise, calls the primary client (OpenRouter) with exponential backoff
        retries. If all attempts fail, falls back to Gemini with grounding enabled.
        """
        should_use_grounding = use_web_search or self._requires_web_search(prompt)

        if should_use_grounding:
            logger.info(
                "Routing to Gemini with Google Search grounding",
                extra={"user_id": user_id, "use_web_search": use_web_search},
            )
            return await self._fallback_client.complete(
                prompt,
                user_id,
                grounding_enabled=True,
            )

        settings = get_settings()

        @retry(
            stop=stop_after_attempt(settings.llm_max_retries),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            before_sleep=before_sleep_log(logger, logging.INFO),
            reraise=True,
        )
        async def call_primary_llm() -> LLMResponse:
            return await self._primary_client.complete(
                prompt,
                user_id,
                grounding_enabled=False,
            )

        try:
            return await call_primary_llm()
        except Exception as exc:
            logger.warning(
                "Primary LLM provider failed; attempting fallback with grounding",
                extra={"user_id": user_id, "error": str(exc)},
                exc_info=True,
            )
            return await self._fallback_client.complete(
                prompt,
                user_id,
                grounding_enabled=True,
            )

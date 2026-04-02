"""LLM routing: hybrid web-grounding path, primary OpenRouter with retries, Gemini fallback."""

import logging
import time
import unicodedata

from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.before_sleep import before_sleep_log

from app.clients.base_llm_client import BaseLLMClient, LLMResponse
from app.config.settings import get_settings
from app.metrics.metrics import (
    llm_calls_total,
    llm_grounding_total,
    llm_fallback_total,
)

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

    def __init__(
        self, primary_client: BaseLLMClient, fallback_client: BaseLLMClient
    ) -> None:
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
        """Complete the prompt using hybrid routing and resilient fallback."""

        # 1. Decision Logic: Should we go straight to Gemini with Grounding?
        should_enable_grounding = use_web_search or self._requires_web_search(prompt)

        if should_enable_grounding:
            logger.info(
                "Routing to Gemini with Google Search grounding",
                extra={
                    "user_id": user_id,
                    "should_enable_grounding": should_enable_grounding,
                },
            )
            start_time = time.perf_counter()
            try:
                # O fallback_client aqui é o Gemini
                response = await self._fallback_client.complete(
                    prompt,
                    user_id,
                    grounding_enabled=True,
                )
                latency_ms = (time.perf_counter() - start_time) * 1000

                # Métricas e Logs usando os novos atributos dos clientes
                llm_calls_total.labels(
                    provider=self._fallback_client.provider_name.lower(),
                    model=response.model,
                    outcome="success",
                ).inc()

                llm_grounding_total.labels(reason="routing").inc()

                logger.info(
                    "llm_request_completed",
                    extra={
                        "user_id": user_id,
                        "model": response.model,
                        "provider": self._fallback_client.provider_name,
                        "latency_ms": latency_ms,
                        "grounding_used": True,
                        "response_id": response.response_id,
                    },
                )
                return response
            except Exception as exc:
                logger.error(
                    "llm_request_failed_during_grounding_route",
                    extra={"user_id": user_id, "error": str(exc)},
                    exc_info=True,
                )
                raise

        # 2. Normal Path: Primary LLM (OpenRouter) with Retries
        settings = get_settings()

        @retry(
            stop=stop_after_attempt(settings.llm_max_retries),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            before_sleep=before_sleep_log(logger, logging.INFO),
            reraise=True,
        )
        async def call_primary_llm() -> LLMResponse:
            start_time = time.perf_counter()
            response = await self._primary_client.complete(
                prompt,
                user_id,
                grounding_enabled=False,
            )
            latency_ms = (time.perf_counter() - start_time) * 1000

            llm_calls_total.labels(
                provider=self._primary_client.provider_name.lower(),
                model=response.model,
                outcome="success",
            ).inc()

            logger.info(
                "llm_request_completed",
                extra={
                    "user_id": user_id,
                    "model": response.model,
                    "provider": self._primary_client.provider_name,
                    "latency_ms": latency_ms,
                    "grounding_used": False,
                    "response_id": response.response_id,
                },
            )
            return response

        try:
            return await call_primary_llm()
        except Exception as exc:
            # 3. Fallback Path: If OpenRouter fails after all retries, try Gemini
            logger.warning(
                "Primary LLM provider failed; attempting fallback with grounding",
                extra={"user_id": user_id, "error": str(exc)},
            )

            llm_fallback_total.labels(
                primary_provider=self._primary_client.provider_name.lower(),
                fallback_provider=self._fallback_client.provider_name.lower(),
            ).inc()

            start_time = time.perf_counter()
            try:
                response = await self._fallback_client.complete(
                    prompt,
                    user_id,
                    grounding_enabled=True,
                )

                logger.info(
                    "llm_request_completed_after_fallback",
                    extra={
                        "user_id": user_id,
                        "model": response.model,
                        "provider": self._fallback_client.provider_name,
                        "grounding_used": True,
                        "response_id": response.response_id,
                        "fallback": True,
                    },
                )
                return response
            except Exception as fallback_exc:
                logger.error(
                    "Critical failure: both primary and fallback LLMs failed",
                    extra={"user_id": user_id, "error": str(fallback_exc)},
                    exc_info=True,
                )
                raise

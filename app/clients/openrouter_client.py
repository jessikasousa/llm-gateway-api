import httpx
import structlog
import time  # Importar time
from typing import List

from app.clients.base_llm_client import (
    BaseLLMClient,
    LLMResponse,
)  # Importar BaseLLMClient e LLMResponse
from app.schemas.chat import (
    ChatCompletionRequest,
    Message,
)  # Importar ChatCompletionRequest e Message
from app.config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class OpenRouterClient(BaseLLMClient):  # Herdar de BaseLLMClient
    """Client for interacting with the OpenRouter API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        if api_key is None:
            settings = get_settings()
            api_key = settings.openrouter_api_key

        self._api_key = api_key
        self._base_url = base_url
        self._name = "OpenRouter"  # Definido aqui

    @property
    def provider_name(self) -> str:
        return self._name

    async def complete(
        self,
        prompt: str,  # Recebe prompt como string
        user_id: str,
        *,
        grounding_enabled: bool = False,  # Manter para consistência, mas OpenRouter não usa diretamente
    ) -> LLMResponse:
        """
        Sends a chat completion request to OpenRouter.
        """
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.app_name,  # Optional: For OpenRouter analytics
            "X-Title": settings.app_name,  # Optional: For OpenRouter analytics
        }

        # Converter o prompt para o formato de mensagens
        messages: List[Message] = [Message(role="user", content=prompt)]

        payload = ChatCompletionRequest(
            model=settings.llm_primary_model,  # Usar o modelo primário das settings
            messages=messages,
            temperature=0.7,  # Valor padrão, pode ser configurável
            max_tokens=1024,  # Valor padrão, pode ser configurável
            stream=False,
            user_id=user_id,  # Passar user_id no payload para OpenRouter
        ).model_dump(exclude_none=True)

        logger.info(
            "openrouter_request",
            model=settings.llm_primary_model,
            messages=[m.model_dump() for m in messages],
            temperature=0.7,
            max_tokens=1024,
            user_id=user_id,
        )

        start = time.monotonic()  # Iniciar o timer

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=60.0
            ) as client:
                response = await client.post(
                    "/chat/completions", headers=headers, json=payload
                )
            response.raise_for_status()
            response_data = response.json()

            latency_ms = int((time.monotonic() - start) * 1000)  # Calcular latência
            content = response_data["choices"][0]["message"]["content"]
            tokens_used = response_data.get("usage", {}).get("total_tokens")
            response_id = response_data.get("id", f"openrouter-resp-{int(time.time())}")
            model = response_data.get("model", settings.llm_primary_model)

            chat_response = LLMResponse(  # Retornar LLMResponse
                content=content,
                model=model,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                response_id=response_id,
            )
            logger.info(
                "openrouter_response",
                response_id=chat_response.response_id,
                model=chat_response.model,
                latency_ms=chat_response.latency_ms,
                tokens_used=chat_response.tokens_used,
                user_id=user_id,
            )
            return chat_response
        except httpx.HTTPStatusError as e:
            logger.error(
                "openrouter_http_error",
                status_code=e.response.status_code,
                response_text=e.response.text,
                error=str(e),
                user_id=user_id,
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "openrouter_request_error",
                error=str(e),
                user_id=user_id,
            )
            raise
        except Exception as e:
            logger.error(
                "openrouter_unexpected_error",
                error=str(e),
                user_id=user_id,
            )
            raise

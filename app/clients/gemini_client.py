"""Google Gemini LLM provider client."""

import time
import structlog
import httpx
from typing import Any, Dict, List

from app.clients.base_llm_client import BaseLLMClient, LLMResponse
from app.config.settings import get_settings
from app.schemas.chat import (
    Message,
)  # Importar Message para _convert_messages_to_gemini_format

logger = structlog.get_logger(__name__)


def _extract_candidate_text(data: dict) -> str:
    """Concatenate text parts from the first candidate."""
    try:
        parts = data["candidates"][0]["content"].get("parts") or []
        return "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except (KeyError, IndexError):
        return ""


def _convert_messages_to_gemini_format(messages: List[Message]) -> List[Dict[str, Any]]:
    """Converts internal Message format to Gemini API format."""
    gemini_messages = []
    for msg in messages:
        # Gemini expects 'user' and 'model' roles. 'assistant' maps to 'model'.
        role = "user" if msg.role == "user" else "model"
        gemini_messages.append({"role": role, "parts": [{"text": msg.content}]})
    return gemini_messages


class GeminiClient(BaseLLMClient):
    """Async HTTP client for Google Gemini API."""

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self._timeout = settings.llm_timeout_seconds
        self._name = "gemini"  # Definido aqui

    @property
    def provider_name(self) -> str:
        return self._name

    async def complete(
        self,
        prompt: str,
        user_id: str,
        *,
        grounding_enabled: bool = False,
    ) -> LLMResponse:
        """Send prompt to Gemini with optional Google Search grounding."""
        url = f"{self._BASE_URL}/{self._model}:generateContent"

        # Convertendo o prompt para o formato de mensagens do Gemini
        messages_for_gemini = _convert_messages_to_gemini_format(
            [Message(role="user", content=prompt)]
        )

        payload: dict = {
            "contents": messages_for_gemini,
            "generationConfig": {  # Adicionado para controle de temperatura/tokens
                "temperature": 0.7,  # Valor padrão, pode ser configurável
                "maxOutputTokens": 1024,  # Valor padrão, pode ser configurável
            },
        }

        if grounding_enabled:
            # Formato correto para Google Search grounding com Gemini API
            payload["tools"] = [{"googleSearch": {}}]
            logger.info(
                "gemini_grounding_enabled", user_id=user_id
            )  # Log para rastreamento

        start = time.monotonic()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self._api_key,
                },
            )
            response.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)
        data = response.json()

        content = _extract_candidate_text(data)
        tokens_used = data.get("usageMetadata", {}).get("totalTokenCount")

        # Gemini não retorna um 'id' direto para a resposta, então geramos um ou usamos um placeholder
        response_id = (
            data.get("candidates", [{}])[0].get("index")
            or f"gemini-resp-{int(time.time())}"
        )

        return LLMResponse(
            content=content,
            model=self._model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            response_id=response_id,
        )

"""Unit tests for ChatService orchestration."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.clients.base_llm_client import LLMResponse
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_process_chat_saves_interaction_after_llm_success() -> None:
    """On successful LLM generation, repository receives mapped fields and returns response."""
    llm_response = LLMResponse(
        content="assistant reply",
        model="openai/gpt-4",
        tokens_used=100,
        latency_ms=50,
    )

    llm_service = AsyncMock(spec=LLMService)
    llm_service.generate = AsyncMock(return_value=llm_response)

    stored = ChatResponse(
        id=uuid4(),
        user_id="user-abc",
        prompt="hello",
        response="assistant reply",
        model="openai/gpt-4",
        timestamp=datetime.now(timezone.utc),
    )

    repository = AsyncMock(spec=ChatRepository)
    repository.save_interaction = AsyncMock(return_value=stored)

    service = ChatService(llm_service, repository)
    payload = ChatRequest.model_validate({"userId": "user-abc", "prompt": "hello"})

    result = await service.process_chat(payload)

    assert result is stored
    llm_service.generate.assert_awaited_once_with(
        "hello",
        "user-abc",
    )
    repository.save_interaction.assert_awaited_once_with(
        user_id="user-abc",
        prompt="hello",
        response="assistant reply",
        model="openai/gpt-4",
        tokens_used=100,
        latency_ms=50,
    )


@pytest.mark.asyncio
async def test_process_chat_does_not_persist_when_llm_fails() -> None:
    """If LLM generation raises, save_interaction is not called."""
    llm_service = AsyncMock(spec=LLMService)
    llm_service.generate = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

    repository = AsyncMock(spec=ChatRepository)
    repository.save_interaction = AsyncMock()

    service = ChatService(llm_service, repository)
    payload = ChatRequest.model_validate({"userId": "u1", "prompt": "x"})

    with pytest.raises(RuntimeError, match="LLM unavailable"):
        await service.process_chat(payload)

    repository.save_interaction.assert_not_called()

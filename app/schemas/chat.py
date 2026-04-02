from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    """Model for a single chat message in conversation context."""

    role: Literal["user", "assistant", "system"]
    content: str


class ChatCompletionRequest(BaseModel):
    """Request payload for OpenRouter chat completion."""

    model: str
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False
    user_id: str | None = None


class ChatCompletionResponse(BaseModel):
    """Optional LLM provider response schema to parse completions."""

    id: str
    model: str
    object: str | None = None
    created: int | None = None
    # fields below are simplified for interface compatibility
    choices: list[dict] | None = None


class ChatRequest(BaseModel):
    """Incoming payload for chat completion."""

    user_id: str = Field(..., alias="userId", min_length=1)
    prompt: str = Field(..., min_length=1, max_length=4000)

    model_config = ConfigDict(populate_by_name=True)


class ChatResponse(BaseModel):
    """Outgoing response schema for chat interactions."""

    id: UUID
    user_id: str = Field(..., serialization_alias="userId")
    prompt: str
    response: str
    model: str
    timestamp: datetime

    model_config = ConfigDict(populate_by_name=True)

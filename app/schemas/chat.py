from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Incoming payload for chat completion."""

    user_id: str = Field(..., alias="userId", min_length=1)
    prompt: str = Field(..., min_length=1, max_length=4000)

    model_config = ConfigDict(populate_by_name=True)


class LLMResponse(BaseModel):
    """Normalized response schema for LLM providers."""

    content: str
    model: str
    tokens_used: int | None = None
    latency_ms: int | None = None


class ChatResponse(BaseModel):
    """Outgoing response schema for chat interactions."""

    id: UUID
    user_id: str = Field(..., alias="userId")
    prompt: str
    response: str
    model: str
    timestamp: datetime

    model_config = ConfigDict(populate_by_name=True)

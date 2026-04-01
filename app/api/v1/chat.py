from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.gemini_client import GeminiClient
from app.clients.openrouter_client import OpenRouterClient
from app.core.database import get_db_session
from app.core.observability import get_logger
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService

router = APIRouter()
logger = get_logger(__name__)


def get_llm_service() -> LLMService:
    """Wire primary (OpenRouter) and fallback (Gemini) clients."""
    return LLMService(OpenRouterClient(), GeminiClient())


def get_chat_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChatRepository:
    """Provide a repository bound to the request-scoped async session."""
    return ChatRepository(session)


def get_chat_service(
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
    repository: Annotated[ChatRepository, Depends(get_chat_repository)],
) -> ChatService:
    """Compose chat orchestration with LLM routing and persistence."""
    return ChatService(llm_service, repository)


@router.post(
    "/chat",
    response_model=ChatResponse,
    response_model_by_alias=True,
)
async def chat_completion(
    payload: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    """Accept a chat request and return the stored interaction payload."""
    try:
        return await service.process_chat(payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "chat_completion_failed",
            error=str(exc),
            user_id=payload.user_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=502,
            detail="LLM gateway could not complete the request",
        ) from exc

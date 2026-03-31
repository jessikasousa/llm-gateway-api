from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


async def get_chat_service() -> ChatService:
    """Dependency stub that will wire ChatService and its dependencies."""
    raise NotImplementedError("Dependency wiring will be implemented later.")


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    payload: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    """Chat endpoint stub that delegates work to service layer."""
    return await service.process_chat(payload)

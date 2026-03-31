from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService


class ChatService:
    """Service stub that will orchestrate chat request processing."""

    def __init__(self, llm_service: LLMService, repository: ChatRepository) -> None:
        self._llm_service: LLMService = llm_service
        self._repository: ChatRepository = repository

    async def process_chat(self, payload: ChatRequest) -> ChatResponse:
        """Process request, call LLM service, and persist interaction."""
        raise NotImplementedError("Chat service logic will be implemented later.")

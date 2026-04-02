from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService


class ChatService:
    """Orchestrate LLM generation and persistence of chat interactions."""

    def __init__(self, llm_service: LLMService, repository: ChatRepository) -> None:
        self._llm_service: LLMService = llm_service
        self._repository: ChatRepository = repository

    async def process_chat(self, payload: ChatRequest) -> ChatResponse:
        """Run LLM generation, then persist; skips persistence if generation fails."""
        llm_result = await self._llm_service.generate(
            payload.prompt,
            payload.user_id,
            use_web_search=payload.use_web_search,
        )
        return await self._repository.save_interaction(
            user_id=payload.user_id,
            prompt=payload.prompt,
            response=llm_result.content,
            model=llm_result.model,
            tokens_used=llm_result.tokens_used,
            latency_ms=llm_result.latency_ms,
        )

from app.schemas.chat import ChatResponse


class ChatRepository:
    """Repository stub that will persist and query chat interactions."""

    async def save_interaction(
        self,
        user_id: str,
        prompt: str,
        response: str,
        model: str,
        tokens_used: int | None,
        latency_ms: int | None,
    ) -> ChatResponse:
        """Persist interaction and return a schema-safe response object."""
        raise NotImplementedError("Chat persistence logic will be implemented later.")

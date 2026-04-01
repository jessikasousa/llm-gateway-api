from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatResponse


class ChatRepository:
    """Persist chat interactions using raw SQL via SQLAlchemy ``text()``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def save_interaction(
        self,
        user_id: str,
        prompt: str,
        response: str,
        model: str,
        tokens_used: int | None,
        latency_ms: int | None,
    ) -> ChatResponse:
        """Insert a row into chat_interactions and return an API-safe payload."""
        interaction_id: str = str(uuid4())
        created_at: datetime = datetime.now(timezone.utc)

        stmt = text(
            """
            INSERT INTO chat_interactions (
                id, user_id, prompt, response, model_used,
                tokens_used, latency_ms, status, created_at
            )
            VALUES (
                :id, :user_id, :prompt, :response, :model_used,
                :tokens_used, :latency_ms, :status, :created_at
            )
            """
        )

        await self._session.execute(
            stmt,
            {
                "id": interaction_id,
                "user_id": user_id,
                "prompt": prompt,
                "response": response,
                "model_used": model,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "status": "completed",
                "created_at": created_at,
            },
        )

        return ChatResponse(
            id=UUID(interaction_id),
            user_id=user_id,
            prompt=prompt,
            response=response,
            model=model,
            timestamp=created_at,
        )

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.chat import router as chat_router
from app.config.settings import get_settings
from app.core.observability import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    configure_logging()
    settings = get_settings()
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        env=settings.app_env
    )
    yield
    logger.info(
        "application_shutdown",
        app_name=settings.app_name,
        env=settings.app_env
    )


settings = get_settings()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return basic service health details."""
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }


app.include_router(chat_router, prefix="/v1", tags=["chat"])
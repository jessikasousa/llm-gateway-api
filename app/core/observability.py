import logging
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from app.config.settings import get_settings


def configure_logging() -> None:
    """Configure structlog renderers by environment."""
    settings = get_settings()
    is_production: bool = settings.app_env.lower() == "production"

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if is_production
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )


def get_logger(name: str = "app") -> BoundLogger:
    """Return a typed structlog logger."""
    return structlog.get_logger(name)

from contextlib import asynccontextmanager
from typing import AsyncIterator
import time

from fastapi import (
    FastAPI,
    Request,
    Response,
    status,
)  # Importar 'status' para usar em JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.api.v1.chat import router as chat_router
from app.config.settings import get_settings
from app.core.observability import configure_logging, get_logger
from app.metrics.metrics import (
    http_requests_total,
    http_errors_total,
    http_request_duration_seconds,
)

logger = get_logger(__name__)


class CustomPrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware for recording HTTP metrics with Prometheus."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request, record metrics, and return response."""
        start_time = time.perf_counter()
        response = None
        status_code = 500  # Default status code for unhandled exceptions

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            # Log the exception before re-raising
            logger.error(
                "unhandled_exception_in_middleware",
                extra={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "error": str(exc),
                },
                exc_info=True,
            )
            status_code = 500  # Ensure status_code is 500 for unhandled exceptions
            raise  # Re-raise the exception to be caught by the global handler
        finally:
            process_time = time.perf_counter() - start_time
            endpoint = request.url.path
            method = request.method

            # Record metrics
            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).observe(process_time)

            if status_code >= 400:
                http_errors_total.labels(
                    method=method, endpoint=endpoint, status_code=status_code
                ).inc()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    configure_logging()
    settings = get_settings()
    logger.info("application_startup", app_name=settings.app_name, env=settings.app_env)
    yield
    logger.info(
        "application_shutdown", app_name=settings.app_name, env=settings.app_env
    )


settings = get_settings()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS - geralmente o middleware mais externo
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Endpoint de métricas (DEVE SER REGISTRADO ANTES DO CustomPrometheusMiddleware)
@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Middleware de métricas customizado (APÓS o endpoint /metrics)
app.add_middleware(CustomPrometheusMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> Response:
    """Global exception handler to log errors and record metrics."""
    endpoint = request.url.path
    method = request.method
    status_code = (
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )  # Usar status.HTTP_500_INTERNAL_SERVER_ERROR

    logger.error(
        "unhandled_exception_global_handler",
        extra={
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "error": str(exc),
        },
        exc_info=True,
    )

    http_errors_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()

    # Retornar JSONResponse para consistência com FastAPI
    from fastapi.responses import JSONResponse

    return JSONResponse(
        content={"error": "Internal Server Error"},
        status_code=status_code,
        media_type="application/json",
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

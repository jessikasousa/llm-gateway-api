"""Test configuration and environment setup."""
import os

# Define todas as variáveis de ambiente ANTES de qualquer import da app
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_NAME", "llm-gateway-api")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/llm_gateway",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
os.environ.setdefault("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("GEMINI_MODEL", "gemini-pro")
os.environ.setdefault("LLM_TIMEOUT_SECONDS", "30")
os.environ.setdefault("LLM_MAX_RETRIES", "3")
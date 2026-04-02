from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_env: str
    app_name: str
    log_level: str

    database_url: str
    redis_url: str

    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_model: str

    gemini_api_key: str
    gemini_model: str

    llm_primary_model: str = "google/gemma-3-4b-it:free"

    llm_timeout_seconds: int
    llm_max_retries: int

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()

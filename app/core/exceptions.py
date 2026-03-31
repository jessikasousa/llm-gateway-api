class LLMUnavailableException(Exception):
    """Raised when no LLM provider is currently available."""


class AllProvidersFailedException(Exception):
    """Raised when all configured LLM providers fail for a request."""


class DatabaseException(Exception):
    """Raised when a database operation fails unexpectedly."""


class InvalidPromptException(Exception):
    """Raised when an input prompt is invalid for processing."""

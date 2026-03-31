from enum import Enum
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class CircuitState(str, Enum):
    """Possible states for the circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker skeleton to protect external provider calls."""

    def __init__(self, failure_threshold: int, recovery_timeout: int) -> None:
        """Initialize with thresholds and timing configuration."""
        self.failure_threshold: int = failure_threshold
        self.recovery_timeout: int = recovery_timeout
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Execute an async operation under circuit breaker control."""
        raise NotImplementedError("Circuit breaker logic will be implemented later.")

    async def _on_success(self) -> None:
        """Handle state transitions for successful operations."""
        raise NotImplementedError("Success handling will be implemented later.")

    async def _on_failure(self) -> None:
        """Handle state transitions for failed operations."""
        raise NotImplementedError("Failure handling will be implemented later.")

class SQSPublisher:
    """Publisher stub that will emit asynchronous events to SQS."""

    async def publish(self, message: dict[str, str]) -> None:
        """Publish an event message to the configured queue."""
        raise NotImplementedError("SQS publishing logic will be implemented later.")

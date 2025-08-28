"""
Network-related exceptions.
"""

from .base import CodeRabbitFetcherError


class APIRateLimitError(CodeRabbitFetcherError):
    """GitHub API rate limit exceeded.

    Raised when the GitHub API rate limit has been exceeded and the
    request cannot be completed.
    """

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        reset_time: int | None = None
    ) -> None:
        """Initialize the rate limit error.

        Args:
            message: Error message
            reset_time: Unix timestamp when rate limit resets (optional)
        """
        details = None
        if reset_time:
            import datetime
            reset_datetime = datetime.datetime.fromtimestamp(reset_time)
            details = f"Rate limit resets at {reset_datetime.isoformat()}"

        super().__init__(message, details)

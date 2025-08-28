"""
Parsing-related exceptions.
"""

from .base import CodeRabbitFetcherError


class InvalidPRUrlError(CodeRabbitFetcherError):
    """Invalid pull request URL format.

    Raised when a provided GitHub pull request URL does not match
    the expected format.
    """

    def __init__(self, message: str) -> None:
        """Initialize the invalid URL error.

        Args:
            message: Error message with URL details
        """
        super().__init__(
            message,
            details="Expected format: https://github.com/owner/repo/pull/123"
        )


class CommentParsingError(CodeRabbitFetcherError):
    """Comment content parsing issues.

    Raised when comment content cannot be parsed or contains
    unexpected format.
    """

    def __init__(self, message: str, comment_id: str | None = None) -> None:
        """Initialize the parsing error.

        Args:
            message: Error message describing the parsing issue
            comment_id: Optional ID of the problematic comment
        """
        details = None
        if comment_id:
            details = f"Failed to parse comment ID: {comment_id}"

        super().__init__(message, details)

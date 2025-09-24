"""
Authentication-related exceptions.
"""

from .base import CodeRabbitFetcherError


class GitHubAuthenticationError(CodeRabbitFetcherError):
    """GitHub CLI authentication issues.

    Raised when the GitHub CLI is not authenticated or authentication
    has expired.
    """

    def __init__(self, message: str = "GitHub CLI authentication required") -> None:
        """Initialize the authentication error.

        Args:
            message: Error message with authentication guidance
        """
        super().__init__(message, details="Run 'gh auth login' to authenticate with GitHub CLI")

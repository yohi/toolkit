"""
Base exception class for CodeRabbit Comment Fetcher.
"""


class CodeRabbitFetcherError(Exception):
    """Base exception for CodeRabbit Fetcher.
    
    All custom exceptions in this application should inherit from this class
    to provide a consistent exception hierarchy.
    """
    
    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            details: Optional additional details about the error
        """
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message

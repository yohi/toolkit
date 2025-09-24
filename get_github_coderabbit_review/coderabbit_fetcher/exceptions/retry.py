"""Retry and resilience-related exceptions."""

from typing import Any, List, Optional

from .base import CodeRabbitFetcherError


class RetryableError(CodeRabbitFetcherError):
    """Base class for errors that can be retried."""

    def __init__(self, message: str, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        details = kwargs.get("details", {})
        if retry_after is not None:
            details["retry_after_seconds"] = retry_after

        super().__init__(message, details=str(details) if details else None)
        self.retry_after = retry_after


class TransientError(RetryableError):
    """Exception for transient errors that should be retried."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            suggestions=[
                "This is a temporary issue that may resolve itself",
                "The operation will be retried automatically",
                "Check network connectivity if retries fail",
            ],
            **kwargs,
        )


class RateLimitError(RetryableError):
    """Exception raised when rate limits are hit."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        limit_type: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.get("details", {})
        if limit_type:
            details["limit_type"] = limit_type

        super().__init__(
            message,
            retry_after=retry_after,
            details=details,
            suggestions=[
                (
                    f"Wait {retry_after} seconds before retrying"
                    if retry_after
                    else "Wait before retrying"
                ),
                "Check API rate limits with 'gh api /rate_limit'",
                "Consider reducing request frequency",
            ],
            **kwargs,
        )


class RetryExhaustedError(CodeRabbitFetcherError):
    """Exception raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_error: Exception,
        error_history: Optional[List[Exception]] = None,
        **kwargs: Any,
    ):
        details = kwargs.get("details", {})
        details.update(
            {
                "attempts": attempts,
                "last_error_type": type(last_error).__name__,
                "last_error_message": str(last_error),
            }
        )

        if error_history:
            details["error_history"] = [
                {"type": type(err).__name__, "message": str(err)} for err in error_history
            ]

        super().__init__(message, details=str(details) if details else None)

        self.attempts = attempts
        self.last_error = last_error
        self.error_history = error_history or []


class TimeoutError(RetryableError):
    """Exception raised when operations timeout."""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ):
        details = kwargs.get("details", {})
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation

        super().__init__(
            message,
            details=details,
            suggestions=[
                "Increase timeout value with --timeout option",
                "Check network connection stability",
                "Try during off-peak hours for better performance",
            ],
            **kwargs,
        )


class CircuitBreakerError(CodeRabbitFetcherError):
    """Exception raised when circuit breaker is open."""

    def __init__(self, message: str, failure_count: int, threshold: int, **kwargs: Any) -> None:
        details = kwargs.get("details", {})
        details.update(
            {
                "failure_count": failure_count,
                "threshold": threshold,
                "failure_rate": failure_count / threshold if threshold > 0 else 0,
            }
        )

        super().__init__(message, details=str(details) if details else None)

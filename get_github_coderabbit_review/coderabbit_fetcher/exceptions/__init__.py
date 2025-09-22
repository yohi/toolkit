"""
Exception classes for CodeRabbit Comment Fetcher.

This module defines the exception hierarchy used throughout the application
for proper error handling and user feedback.
"""

from .analysis import (
    CodeRabbitDetectionError,
    CommentAnalysisError,
    CommentFilteringError,
    ResolvedMarkerError,
    ReviewProcessingError,
    SummaryProcessingError,
    ThreadProcessingError,
)
from .auth import GitHubAuthenticationError
from .base import CodeRabbitFetcherError
from .network import APIRateLimitError, NetworkError
from .parsing import CommentParsingError, InvalidPRUrlError
from .persona import PersonaFileError, PersonaLoadError, PersonaValidationError
from .retry import (
    CircuitBreakerError,
    RateLimitError,
    RetryableError,
    RetryExhaustedError,
    TimeoutError,
    TransientError,
)
from .utils import (
    chain_exceptions,
    create_error_report,
    create_error_summary,
    format_exception_for_user,
    get_error_category,
    is_recoverable_error,
    log_exception_details,
)
from .validation import (
    ConfigurationValidationError,
    FileValidationError,
    ParameterValidationError,
    URLValidationError,
    ValidationError,
)

__all__ = [
    # Base exception
    "CodeRabbitFetcherError",
    # Authentication exceptions
    "GitHubAuthenticationError",
    # Network exceptions
    "NetworkError",
    "APIRateLimitError",
    # Parsing exceptions
    "CommentParsingError",
    "InvalidPRUrlError",
    # Persona exceptions
    "PersonaFileError",
    "PersonaLoadError",
    "PersonaValidationError",
    # Validation exceptions
    "ValidationError",
    "ConfigurationValidationError",
    "URLValidationError",
    "FileValidationError",
    "ParameterValidationError",
    # Analysis exceptions
    "CommentAnalysisError",
    "CodeRabbitDetectionError",
    "ThreadProcessingError",
    "ResolvedMarkerError",
    "CommentFilteringError",
    "SummaryProcessingError",
    "ReviewProcessingError",
    # Retry and resilience exceptions
    "RetryableError",
    "TransientError",
    "RateLimitError",
    "RetryExhaustedError",
    "TimeoutError",
    "CircuitBreakerError",
    # Utility functions
    "format_exception_for_user",
    "create_error_summary",
    "log_exception_details",
    "is_recoverable_error",
    "get_error_category",
    "create_error_report",
    "chain_exceptions",
]

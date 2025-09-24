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
    "APIRateLimitError",
    "NetworkError",
    # Parsing exceptions
    "CommentParsingError",
    "InvalidPRUrlError",
    # Persona exceptions
    "PersonaFileError",
    "PersonaLoadError",
    "PersonaValidationError",
    # Validation exceptions
    "ConfigurationValidationError",
    "FileValidationError",
    "ParameterValidationError",
    "URLValidationError",
    "ValidationError",
    # Analysis exceptions
    "CodeRabbitDetectionError",
    "CommentAnalysisError",
    "CommentFilteringError",
    "ResolvedMarkerError",
    "ReviewProcessingError",
    "SummaryProcessingError",
    "ThreadProcessingError",
    # Retry and resilience exceptions
    "CircuitBreakerError",
    "RateLimitError",
    "RetryExhaustedError",
    "RetryableError",
    "TimeoutError",
    "TransientError",
    # Utility functions
    "chain_exceptions",
    "create_error_report",
    "create_error_summary",
    "format_exception_for_user",
    "get_error_category",
    "is_recoverable_error",
    "log_exception_details",
]

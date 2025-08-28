"""
Exception classes for CodeRabbit Comment Fetcher.

This module defines the exception hierarchy used throughout the application
for proper error handling and user feedback.
"""

from .base import CodeRabbitFetcherError
from .auth import GitHubAuthenticationError
from .network import APIRateLimitError
from .parsing import CommentParsingError, InvalidPRUrlError
from .persona import PersonaFileError, PersonaLoadError, PersonaValidationError
from .validation import (
    ValidationError,
    ConfigurationValidationError,
    URLValidationError,
    FileValidationError,
    ParameterValidationError
)
from .analysis import (
    CommentAnalysisError,
    CodeRabbitDetectionError,
    ThreadProcessingError,
    ResolvedMarkerError,
    CommentFilteringError,
    SummaryProcessingError,
    ReviewProcessingError
)
from .retry import (
    RetryableError,
    TransientError,
    RateLimitError,
    RetryExhaustedError,
    TimeoutError,
    CircuitBreakerError
)
from .utils import (
    format_exception_for_user,
    create_error_summary,
    log_exception_details,
    is_recoverable_error,
    get_error_category,
    create_error_report,
    chain_exceptions
)

__all__ = [
    # Base exception
    "CodeRabbitFetcherError",
    
    # Authentication exceptions
    "GitHubAuthenticationError",
    
    # Network exceptions
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

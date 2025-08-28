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

__all__ = [
    "CodeRabbitFetcherError",
    "GitHubAuthenticationError",
    "APIRateLimitError",
    "CommentParsingError",
    "InvalidPRUrlError",
    "PersonaFileError",
    "PersonaLoadError",
    "PersonaValidationError",
]

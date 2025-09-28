"""
Formatters package for CodeRabbit Comment Fetcher.

This package provides various output formatters for processing and displaying
CodeRabbit comments in different formats.
"""

from .base_formatter import BaseFormatter
from .markdown_formatter import MarkdownFormatter
from .json_formatter import JSONFormatter
from .plaintext_formatter import PlainTextFormatter

__version__ = "1.0.0"

__all__ = [
    "BaseFormatter",
    "MarkdownFormatter",
    "JSONFormatter",
    "PlainTextFormatter",
]

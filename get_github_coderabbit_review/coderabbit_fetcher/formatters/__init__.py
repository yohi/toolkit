"""
Formatters package for CodeRabbit Comment Fetcher.

This package provides various output formatters for processing and displaying
CodeRabbit comments in different formats.
"""

from .base import BaseFormatter
from .markdown import MarkdownFormatter
from .json_formatter import JSONFormatter
from .plain import PlainTextFormatter

__version__ = "1.0.0"

__all__ = [
    "BaseFormatter",
    "MarkdownFormatter", 
    "JSONFormatter",
    "PlainTextFormatter",
]

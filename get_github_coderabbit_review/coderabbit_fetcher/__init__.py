"""
CodeRabbit Comment Fetcher

A Python tool for fetching and formatting CodeRabbit comments from GitHub pull requests.
Provides AI-optimized output formatting and integrates with GitHub CLI for authentication.
"""

__version__ = "1.0.0"
__author__ = "CodeRabbit Fetcher Team"
__email__ = "support@coderabbit-fetcher.dev"

from .cli import main
from .exceptions import CodeRabbitFetcherError
from .models import AnalyzedComments, SummaryComment, ReviewComment

__all__ = [
    "main",
    "CodeRabbitFetcherError",
    "AnalyzedComments",
    "SummaryComment", 
    "ReviewComment",
]

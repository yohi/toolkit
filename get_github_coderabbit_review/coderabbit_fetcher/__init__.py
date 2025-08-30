"""
CodeRabbit Comment Fetcher

A Python tool for fetching and formatting CodeRabbit comments from GitHub pull requests.
Provides AI-optimized output formatting and integrates with GitHub CLI for authentication.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cli.main import main

__version__ = "1.0.0"
__author__ = "CodeRabbit Fetcher Team"
__email__ = "support@coderabbit-fetcher.dev"

from .exceptions import CodeRabbitFetcherError
from .models import (
    AnalyzedComments, 
    SummaryComment, 
    ReviewComment,
    ActionableComment,
    AIAgentPrompt,
    ThreadContext,
    CommentMetadata,
)

__all__ = [
    "main",
    "CodeRabbitFetcherError",
    "AnalyzedComments",
    "SummaryComment",
    "ReviewComment",
    "ActionableComment",
    "AIAgentPrompt",
    "ThreadContext", 
    "CommentMetadata",
]

# Lazily expose CLI entry to avoid import-time side effects.
def __getattr__(name: str):
    if name == "main":
        from .cli.main import main as _main
        return _main
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

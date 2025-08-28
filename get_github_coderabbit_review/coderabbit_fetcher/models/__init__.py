"""
Data models for CodeRabbit Comment Fetcher.

This module defines the core data structures used throughout the application
for representing CodeRabbit comments and analysis results.
"""

from .analyzed_comments import AnalyzedComments
from .comment_metadata import CommentMetadata
from .summary_comment import SummaryComment, ChangeEntry
from .review_comment import ReviewComment
from .actionable_comment import ActionableComment
from .ai_agent_prompt import AIAgentPrompt
from .thread_context import ThreadContext

__all__ = [
    "AnalyzedComments",
    "CommentMetadata",
    "SummaryComment",
    "ChangeEntry", 
    "ReviewComment",
    "ActionableComment",
    "AIAgentPrompt",
    "ThreadContext",
]

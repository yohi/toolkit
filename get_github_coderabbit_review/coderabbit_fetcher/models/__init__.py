"""
Data models for CodeRabbit Comment Fetcher.

This module defines the core data structures used throughout the application
for representing CodeRabbit comments and analysis results.
"""

from .actionable_comment import ActionableComment, CommentType, Priority
from .ai_agent_prompt import AIAgentPrompt
from .analyzed_comments import AnalyzedComments
from .comment_metadata import CommentMetadata
from .review_comment import BasicReviewComment, NitpickComment, OutsideDiffComment, ReviewComment
from .summary_comment import ChangeEntry, SummaryComment
from .thread_context import ResolutionStatus, ThreadContext

__all__ = [
    "AnalyzedComments",
    "CommentMetadata",
    "SummaryComment",
    "ChangeEntry",
    "ReviewComment",
    "BasicReviewComment",
    "NitpickComment",
    "OutsideDiffComment",
    "ActionableComment",
    "CommentType",
    "Priority",
    "AIAgentPrompt",
    "ThreadContext",
    "ResolutionStatus",
]

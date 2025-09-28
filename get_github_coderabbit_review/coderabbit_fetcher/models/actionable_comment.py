"""
Actionable comment data model.
"""

from typing import Optional, Any, Dict
from enum import Enum

from pydantic import model_validator
from .base import BaseCodeRabbitModel
from .ai_agent_prompt import AIAgentPrompt
from .thread_context import ThreadContext


class CommentType(str, Enum):
    """Types of actionable comments."""
    NITPICK = "nitpick"
    POTENTIAL_ISSUE = "potential_issue"
    REFACTOR_SUGGESTION = "refactor_suggestion"
    OUTSIDE_DIFF = "outside_diff"
    GENERAL = "general"


class Priority(str, Enum):
    """Priority levels for actionable comments."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionableComment(BaseCodeRabbitModel):
    """Actionable comment from CodeRabbit review.

    Represents a specific issue or suggestion that requires
    developer attention or action.
    """

    comment_id: str
    file_path: str
    line_range: str
    issue_description: str
    comment_type: CommentType = CommentType.GENERAL
    priority: Priority = Priority.MEDIUM
    ai_agent_prompt: Optional[AIAgentPrompt] = None
    thread_context: Optional[ThreadContext] = None
    raw_content: str
    is_resolved: bool = False
    
    @model_validator(mode="before")
    @classmethod
    def normalize_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize input data by auto-detecting priority and comment_type."""
        # Auto-detect priority from content if not provided or explicitly None
        if data.get("priority") is None:
            data["priority"] = cls._detect_priority(
                data.get("issue_description", ""),
                data.get("raw_content", "")
            )
        
        # Auto-detect comment type if not provided or explicitly None
        if data.get("comment_type") is None:
            data["comment_type"] = cls._detect_comment_type(
                data.get("raw_content", "")
            )
        
        return data
    
    @staticmethod
    def _detect_priority(description: str, raw_content: str) -> Priority:
        """Detect priority level from comment content.

        Args:
            description: Issue description
            raw_content: Full comment content

        Returns:
            Detected priority level
        """
        content = (description + " " + raw_content).lower()

        # High priority keywords
        high_keywords = [
            "security", "vulnerability", "critical", "urgent", "fatal",
            "error", "exception", "crash", "fail", "broken", "bug"
        ]

        # Low priority keywords
        low_keywords = [
            "nitpick", "style", "formatting", "whitespace", "comment",
            "documentation", "typo", "minor", "suggestion"
        ]

        if any(keyword in content for keyword in high_keywords):
            return Priority.HIGH
        elif any(keyword in content for keyword in low_keywords):
            return Priority.LOW

        return Priority.MEDIUM

    @staticmethod
    def _detect_comment_type(raw_content: str) -> CommentType:
        """Detect comment type from raw content.

        Args:
            raw_content: Full comment content

        Returns:
            Detected comment type
        """
        content = raw_content.lower()

        if "🧹 nitpick" in content:
            return CommentType.NITPICK
        elif "⚠️ potential issue" in content:
            return CommentType.POTENTIAL_ISSUE
        elif "🛠️ refactor suggestion" in content:
            return CommentType.REFACTOR_SUGGESTION
        elif "outside diff range" in content:
            return CommentType.OUTSIDE_DIFF

        return CommentType.GENERAL

    @property
    def has_ai_prompt(self) -> bool:
        """Check if comment has AI agent prompt.

        Returns:
            True if comment contains AI agent prompt
        """
        return self.ai_agent_prompt is not None

    @property
    def is_high_priority(self) -> bool:
        """Check if comment is high priority.

        Returns:
            True if comment has high priority
        """
        return self.priority == Priority.HIGH

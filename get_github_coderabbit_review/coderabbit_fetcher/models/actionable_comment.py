"""
Actionable comment data model.
"""

from typing import Optional
from enum import Enum

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

    def __init__(self, **data) -> None:
        """Initialize actionable comment with auto-detected priority."""
        # Auto-detect priority from content if not provided
        if "priority" not in data:
            data["priority"] = self._detect_priority(
                data.get("issue_description", ""),
                data.get("raw_content", "")
            )

        # Auto-detect comment type if not provided
        if "comment_type" not in data:
            data["comment_type"] = self._detect_comment_type(
                data.get("raw_content", "")
            )

        super().__init__(**data)

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

    @property
    def title(self) -> str:
        """Generate a title from issue description.

        Returns:
            Title string derived from issue description
        """
        if not self.issue_description:
            return "CodeRabbit Comment"
        
        # Take the first sentence or first 80 characters as title
        first_sentence = self.issue_description.split('.')[0].strip()
        if len(first_sentence) > 80:
            # If first sentence is too long, truncate it
            return first_sentence[:77] + "..."
        return first_sentence if first_sentence else "CodeRabbit Comment"

    @property
    def line_number(self) -> Optional[str]:
        """Extract line number from line_range.

        Returns:
            Line number string or None if not available
        """
        if not self.line_range:
            return None
        
        # Handle different line range formats like "123", "123-125", etc.
        if '-' in self.line_range:
            # Range format, return the first line number
            return self.line_range.split('-')[0].strip()
        else:
            # Single line format
            return self.line_range.strip()

    @property
    def issue(self) -> str:
        """Return the main issue/content for this comment."""
        return self.issue_description

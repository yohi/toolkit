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
    proposed_diff: str = ""
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

        # Auto-extract diff if not provided
        if "proposed_diff" not in data or not data.get("proposed_diff"):
            from ..utils.diff_extractor import DiffExtractor
            data["proposed_diff"] = DiffExtractor.extract_diff_blocks(
                data.get("raw_content", "")
            )

        super().__init__(**data)

    @staticmethod
    def _detect_priority(description: str, raw_content: str) -> Priority:
        """Detect priority level from comment content with Phase 2 enhanced classification.

        Args:
            description: Issue description
            raw_content: Full comment content

        Returns:
            Detected priority level
        """
        content = (description + " " + raw_content).lower()

        # Phase 2: Enhanced priority classification with weighted scoring
        priority_score = 0

        # Critical security issues (Highest priority)
        critical_security_keywords = [
            "security", "vulnerability", "exploit", "injection", "xss", "csrf",
            "authentication bypass", "privilege escalation", "remote code execution",
            "sql injection", "command injection", "path traversal", "data leak",
            "sensitive data", "credentials", "password", "token", "secret"
        ]

        # High priority technical issues
        high_technical_keywords = [
            "critical", "fatal", "crash", "exception", "error", "fail", "broken",
            "deadlock", "race condition", "memory leak", "performance", "timeout",
            "data corruption", "data loss", "infinite loop", "stack overflow",
            "null pointer", "buffer overflow", "out of bounds"
        ]

        # Medium priority functional issues
        medium_functional_keywords = [
            "bug", "issue", "problem", "incorrect", "wrong behavior", "unexpected",
            "not working", "malfunction", "regression", "compatibility",
            "inconsistent", "missing functionality", "logic error"
        ]

        # Low priority style and minor issues
        low_priority_keywords = [
            "nitpick", "style", "formatting", "whitespace", "indentation", "comment",
            "documentation", "typo", "minor", "suggestion", "cleanup", "refactor",
            "optimization", "improvement", "convention", "naming", "readability"
        ]

        # Phase 2: Weighted scoring system
        for keyword in critical_security_keywords:
            if keyword in content:
                priority_score += 10  # Highest weight for security

        for keyword in high_technical_keywords:
            if keyword in content:
                priority_score += 5   # High weight for technical issues

        for keyword in medium_functional_keywords:
            if keyword in content:
                priority_score += 2   # Medium weight for functional issues

        for keyword in low_priority_keywords:
            if keyword in content:
                priority_score -= 3   # Negative weight for minor issues

        # Phase 2: CodeRabbit emoji-based classification
        emoji_weights = {
            "⚠️": 4,     # Warning - high priority
            "🛠️": 3,     # Refactor - medium-high priority
            "🔒": 8,     # Security - critical priority
            "💀": 7,     # Dangerous - high priority
            "🚨": 6,     # Alert - high priority
            "🧹": -2,    # Nitpick - low priority
            "💡": 1,     # Suggestion - low-medium priority
            "📝": -1,    # Documentation - low priority
            "✨": 0      # Enhancement - neutral
        }

        for emoji, weight in emoji_weights.items():
            if emoji in raw_content:
                priority_score += weight

        # Phase 2: Context-based adjustments
        # File type considerations
        if any(ext in content for ext in ['.config', '.env', '.secret', '.key']):
            priority_score += 3  # Config/secret files are more important

        if any(ext in content for ext in ['.test', '.spec', 'test_', '_test']):
            priority_score -= 1  # Test files are slightly lower priority

        if any(ext in content for ext in ['.md', '.txt', '.doc', 'readme']):
            priority_score -= 2  # Documentation files are lower priority

        # Code complexity indicators
        complexity_indicators = [
            'complex', 'complicated', 'difficult', 'hard to', 'confusing',
            'maintainability', 'scalability', 'architecture'
        ]

        for indicator in complexity_indicators:
            if indicator in content:
                priority_score += 1

        # Phase 2: Final priority determination with thresholds
        if priority_score >= 8:
            return Priority.HIGH
        elif priority_score >= 3:
            return Priority.MEDIUM
        elif priority_score <= -3:
            return Priority.LOW
        else:
            return Priority.MEDIUM  # Default for unclear cases

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
    def has_diff(self) -> bool:
        """Check if comment has proposed diff.

        Returns:
            True if comment has proposed diff
        """
        return bool(self.proposed_diff and self.proposed_diff.strip())

    @property
    def issue(self) -> str:
        """Return the main issue/content for this comment."""
        return self.issue_description

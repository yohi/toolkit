"""Base formatter abstract class for CodeRabbit comment output."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List

from ..models import (
    ActionableComment,
    AIAgentPrompt,
    AnalyzedComments,
    NitpickComment,
    OutsideDiffComment,
    ThreadContext,
)


class BaseFormatter(ABC):
    """Abstract base class for comment output formatters."""

    def __init__(self):
        """Initialize base formatter."""
        self.timestamp = datetime.now()

    @abstractmethod
    def format(self, persona: str, analyzed_comments: AnalyzedComments, quiet: bool = False) -> str:
        """Format analyzed comments with persona.

        Args:
            persona: AI persona prompt string
            analyzed_comments: Analyzed CodeRabbit comments
            quiet: Use quiet mode for minimal AI-optimized output

        Returns:
            Formatted output string
        """
        pass

    def format_ai_agent_prompt(self, prompt: AIAgentPrompt) -> str:
        """Format AI agent prompt with special handling.

        Args:
            prompt: AI agent prompt to format

        Returns:
            Formatted AI agent prompt string
        """
        # Base implementation - can be overridden by subclasses
        sections = []

        if prompt.description:
            sections.append(f"Description: {prompt.description}")

        if prompt.file_path:
            sections.append(f"File: {prompt.file_path}")

        if prompt.line_range:
            sections.append(f"Lines: {prompt.line_range}")

        if prompt.code_block:
            sections.append(f"Code Block:\n{prompt.code_block}")

        return "\n".join(sections)

    def format_thread_context(self, thread: ThreadContext) -> str:
        """Format thread context following Claude 4 best practices.

        Args:
            thread: Thread context to format

        Returns:
            Formatted thread context string
        """
        # Base implementation with Claude 4 structured format
        sections = []

        # Thread Overview
        sections.append("## Thread Context")
        sections.append(f"**Thread ID**: {getattr(thread, 'thread_id', 'N/A')}")
        sections.append(f"**Resolution Status**: {thread.resolution_status}")
        sections.append(
            f"**Comment Count**: {getattr(thread, 'comment_count', len(thread.chronological_order))}"
        )

        # File Context
        if hasattr(thread, "file_context") and thread.file_context:
            sections.append(f"**File**: {thread.file_context}")

        if hasattr(thread, "line_context") and thread.line_context:
            sections.append(f"**Line**: {thread.line_context}")

        # Participants
        if hasattr(thread, "participants") and thread.participants:
            participants_str = ", ".join(thread.participants)
            sections.append(f"**Participants**: {participants_str}")

        # AI Summary
        if hasattr(thread, "ai_summary") and thread.ai_summary:
            sections.append("### AI Summary")
            sections.append(thread.ai_summary)

        # Contextual Summary (fallback)
        elif thread.contextual_summary:
            sections.append("### Summary")
            sections.append(thread.contextual_summary)

        return "\n".join(sections)

    def format_actionable_comments(self, comments: List[ActionableComment]) -> str:
        """Format actionable comments.

        Args:
            comments: List of actionable comments

        Returns:
            Formatted actionable comments string
        """
        if not comments:
            return ""

        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"{i}. **{comment.title}**")
            if comment.issue_description:
                sections.append(f"   {comment.issue_description}")
            if comment.file_path:
                sections.append(f"   File: {comment.file_path}")
            if comment.line_number:
                sections.append(f"   Line: {comment.line_number}")
            sections.append("")  # Empty line for spacing

        return "\n".join(sections)

    def format_nitpick_comments(self, comments: List[NitpickComment]) -> str:
        """Format nitpick comments.

        Args:
            comments: List of nitpick comments

        Returns:
            Formatted nitpick comments string
        """
        if not comments:
            return ""

        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"{i}. {comment.suggestion}")
            if comment.file_path:
                sections.append(f"   File: {comment.file_path}")
            if comment.line_number:
                sections.append(f"   Line: {comment.line_number}")
            sections.append("")  # Empty line for spacing

        return "\n".join(sections)

    def format_outside_diff_comments(self, comments: List[OutsideDiffComment]) -> str:
        """Format outside diff range comments.

        Args:
            comments: List of outside diff comments

        Returns:
            Formatted outside diff comments string
        """
        if not comments:
            return ""

        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"{i}. **{comment.issue}**")
            if comment.issue_description:
                sections.append(f"   {comment.issue_description}")
            if comment.file_path:
                sections.append(f"   File: {comment.file_path}")
            if comment.line_range:
                sections.append(f"   Lines: {comment.line_range}")
            sections.append("")  # Empty line for spacing

        return "\n".join(sections)

    def format_metadata(self, analyzed_comments: AnalyzedComments) -> Dict[str, Any]:
        """Generate formatting metadata.

        Args:
            analyzed_comments: Analyzed comments to extract metadata from

        Returns:
            Dictionary containing formatting metadata
        """
        total_comments = 0
        total_threads = 0

        if analyzed_comments.summary_comments:
            total_comments += len(analyzed_comments.summary_comments)

        if analyzed_comments.review_comments:
            total_comments += len(analyzed_comments.review_comments)

        if analyzed_comments.unresolved_threads:
            total_threads = len(analyzed_comments.unresolved_threads)

        return {
            "timestamp": self.timestamp.isoformat(),
            "total_comments": total_comments,
            "total_threads": total_threads,
            "summary_count": (
                len(analyzed_comments.summary_comments) if analyzed_comments.summary_comments else 0
            ),
            "review_count": (
                len(analyzed_comments.review_comments) if analyzed_comments.review_comments else 0
            ),
            "formatter_type": self.__class__.__name__,
        }

    def get_visual_markers(self) -> Dict[str, str]:
        """Get visual markers for different comment types.

        Returns:
            Dictionary mapping comment types to visual markers
        """
        return {
            "actionable": "🔥",
            "nitpick": "🧹",
            "outside_diff": "⚠️",
            "ai_prompt": "🤖",
            "security": "🔒",
            "performance": "⚡",
            "bug": "🐛",
            "enhancement": "✨",
            "documentation": "📝",
            "refactor": "♻️",
        }

    def _sanitize_content(self, content: str) -> str:
        """Sanitize content for safe output.

        Args:
            content: Content to sanitize

        Returns:
            Sanitized content string
        """
        if not content:
            return ""

        # Remove potentially problematic characters but preserve formatting
        sanitized = content.replace("\x00", "")  # Remove null bytes
        sanitized = sanitized.replace("\r\n", "\n")  # Normalize line endings
        sanitized = sanitized.replace("\r", "\n")  # Handle Mac line endings

        return sanitized

    def _truncate_content(self, content: str, max_length: int = 1000) -> str:
        """Truncate content if too long.

        Args:
            content: Content to truncate
            max_length: Maximum allowed length

        Returns:
            Truncated content with ellipsis if needed
        """
        if not content or len(content) <= max_length:
            return content

        return content[: max_length - 3] + "..."

    def _extract_priority_level(self, comment_content: str) -> str:
        """Extract priority level from comment content.

        Args:
            comment_content: Comment content to analyze

        Returns:
            Priority level string (High, Medium, Low)
        """
        content_lower = comment_content.lower()

        # High priority indicators
        high_priority_keywords = [
            "critical",
            "security",
            "vulnerability",
            "error",
            "exception",
            "breaking",
            "urgent",
            "important",
            "must fix",
            "required",
        ]

        # Medium priority indicators
        medium_priority_keywords = [
            "should",
            "recommend",
            "suggest",
            "improve",
            "optimize",
            "performance",
            "consider",
            "enhancement",
        ]

        # Check for high priority
        if any(keyword in content_lower for keyword in high_priority_keywords):
            return "High"

        # Check for medium priority
        if any(keyword in content_lower for keyword in medium_priority_keywords):
            return "Medium"

        # Default to low priority
        return "Low"

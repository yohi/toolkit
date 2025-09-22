"""
Thread context data model.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .base import BaseCodeRabbitModel


class ResolutionStatus(str, Enum):
    """Status of comment thread resolution."""

    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    PENDING = "pending"


class ThreadContext(BaseCodeRabbitModel):
    """Context information for a comment thread.

    Provides chronological ordering and contextual information
    about a comment thread for AI consumption.
    """

    thread_id: str
    root_comment_id: str
    file_context: str = ""
    line_context: str = ""
    participants: List[str] = []
    comment_count: int = 0
    coderabbit_comment_count: int = 0
    is_resolved: bool = False
    context_summary: str = ""
    ai_summary: str = ""
    chronological_comments: List[Dict[str, Any]] = []

    # Legacy fields for backward compatibility
    main_comment: Optional[Dict[str, Any]] = None
    replies: List[Dict[str, Any]] = []
    resolution_status: ResolutionStatus = ResolutionStatus.UNRESOLVED
    chronological_order: List[Dict[str, Any]] = []
    contextual_summary: str = ""

    def __init__(self, **data) -> None:
        """Initialize thread context with auto-generated summary."""
        super().__init__(**data)

        # Sync new fields with legacy fields for backward compatibility
        if self.chronological_comments and not self.chronological_order:
            self.chronological_order = self.chronological_comments

        if self.context_summary and not self.contextual_summary:
            self.contextual_summary = self.context_summary

        if self.is_resolved:
            self.resolution_status = ResolutionStatus.RESOLVED

        # Set main_comment from chronological_comments if available
        if self.chronological_comments and not self.main_comment:
            self.main_comment = self.chronological_comments[0]
            if len(self.chronological_comments) > 1:
                self.replies = self.chronological_comments[1:]

        # Auto-generate contextual summary if not provided
        if not self.contextual_summary and not self.context_summary:
            self.contextual_summary = self._generate_contextual_summary()

        # Auto-sort chronological order if not provided
        if not self.chronological_order and self.main_comment:
            self.chronological_order = self._build_chronological_order()

    def _generate_contextual_summary(self) -> str:
        """Generate a contextual summary of the thread.

        Returns:
            Human-readable summary of the thread context
        """
        total_comments = 1 + len(self.replies)
        main_author = self.main_comment.get("user", {}).get("login", "unknown")

        summary_parts = [
            f"Thread with {total_comments} comment(s)",
            f"Started by {main_author}",
            f"Status: {self.resolution_status.value if hasattr(self.resolution_status, 'value') else str(self.resolution_status)}",
        ]

        if self.replies:
            reply_authors = set(
                reply.get("user", {}).get("login", "unknown") for reply in self.replies
            )
            summary_parts.append(f"Contributors: {', '.join(reply_authors)}")

        return " | ".join(summary_parts)

    def _build_chronological_order(self) -> List[Dict[str, Any]]:
        """Build chronological order of all comments in thread.

        Returns:
            List of comments sorted by creation time
        """
        all_comments = [self.main_comment] + self.replies

        # Sort by created_at timestamp
        return sorted(all_comments, key=lambda comment: comment.get("created_at", ""))

    @property
    def participant_count(self) -> int:
        """Get number of unique participants in thread.

        Returns:
            Number of unique users who commented
        """
        authors = {self.main_comment.get("user", {}).get("login")}
        authors.update(reply.get("user", {}).get("login") for reply in self.replies)
        # Remove None values
        authors.discard(None)
        return len(authors)

    @property
    def latest_activity(self) -> Optional[datetime]:
        """Get timestamp of latest activity in thread.

        Returns:
            Datetime of most recent comment or None
        """
        if not self.chronological_order:
            return None

        latest_comment = self.chronological_order[-1]
        created_at = latest_comment.get("created_at")

        if created_at:
            try:
                return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return None

    def add_reply(self, reply: Dict[str, Any]) -> None:
        """Add a reply to the thread.

        Args:
            reply: Reply comment data
        """
        self.replies.append(reply)
        self.chronological_order = self._build_chronological_order()
        self.contextual_summary = self._generate_contextual_summary()

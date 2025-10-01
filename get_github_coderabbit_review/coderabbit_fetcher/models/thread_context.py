"""
Thread context data model.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

from pydantic import Field
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
    main_comment: Dict[str, Any]
    replies: List[Dict[str, Any]] = Field(default_factory=list)
    resolution_status: ResolutionStatus = ResolutionStatus.UNRESOLVED
    chronological_order: List[Dict[str, Any]] = Field(default_factory=list)
    contextual_summary: str = ""

    def __init__(self, **data) -> None:
        """Initialize thread context with auto-generated summary."""
        super().__init__(**data)
        # Auto-generate contextual summary if not provided
        if not self.contextual_summary:
            self.contextual_summary = self._generate_contextual_summary()

        # Auto-sort chronological order if not provided
        if not self.chronological_order:
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
            f"Status: {self.resolution_status}",
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

    # Backward compatibility properties
    @property
    def root_comment_id(self) -> str:
        """Get root comment ID for backward compatibility."""
        return str(self.main_comment.get("id", ""))

    @property
    def file_context(self) -> str:
        """Get file context for backward compatibility."""
        return self.main_comment.get("path", "")

    @property
    def line_context(self) -> str:
        """Get line context for backward compatibility."""
        # Check for direct line field first
        line = self.main_comment.get("line")
        if line is not None:
            return str(line)

        # Check for start_line/end_line range
        start_line = self.main_comment.get("start_line")
        end_line = self.main_comment.get("end_line")
        if start_line is not None and end_line is not None:
            return f"{start_line}-{end_line}"
        elif start_line is not None:
            return str(start_line)

        # Extract line information from diff_hunk, url or other fields
        diff_hunk = self.main_comment.get("diff_hunk", "")
        if diff_hunk and "@@ -" in diff_hunk:
            # Extract line number from diff hunk
            try:
                line_info = diff_hunk.split("@@")[1].strip().split()[1]
                if line_info.startswith("+"):
                    return line_info[1:].split(",")[0]
            except (IndexError, ValueError):
                pass

        # Try to extract from other sources
        url = self.main_comment.get("url", "")
        if "#L" in url:
            try:
                return url.split("#L")[1].split("-")[0]
            except IndexError:
                pass

        # Try to extract line numbers from body
        body = self.main_comment.get("body", "")
        import re

        line_match = re.search(r"line (\d+)", body.lower())
        if line_match:
            return line_match.group(1)

        return ""

    @property
    def participants(self) -> List[str]:
        """Get participants list for backward compatibility."""
        authors = {self.main_comment.get("user", {}).get("login")}
        authors.update(reply.get("user", {}).get("login") for reply in self.replies)
        # Remove None values and sort
        authors.discard(None)
        return sorted(list(authors))

    @property
    def comment_count(self) -> int:
        """Get comment count for backward compatibility."""
        return len(self.chronological_order)

    @property
    def coderabbit_comment_count(self) -> int:
        """Get CodeRabbit comment count for backward compatibility."""
        coderabbit_author = "coderabbitai[bot]"
        count = 0
        for comment in self.chronological_order:
            if comment.get("user", {}).get("login") == coderabbit_author:
                count += 1
        return count

    @property
    def is_resolved(self) -> bool:
        """Get resolution status as boolean for backward compatibility."""
        return self.resolution_status == ResolutionStatus.RESOLVED

    @property
    def context_summary(self) -> str:
        """Get context summary for backward compatibility."""
        return self.contextual_summary

    @property
    def ai_summary(self) -> str:
        """Get AI summary for backward compatibility."""
        # Generate basic AI summary from available data
        return f"Thread: {self.contextual_summary}"

    @property
    def chronological_comments(self) -> List[Dict[str, Any]]:
        """Get chronological comments for backward compatibility."""
        return self.chronological_order

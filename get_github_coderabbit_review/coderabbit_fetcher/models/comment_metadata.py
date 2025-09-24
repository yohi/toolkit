"""
Metadata for comment analysis results.
"""

from datetime import datetime
from typing import Dict, Optional

from .base import BaseCodeRabbitModel


class CommentMetadata(BaseCodeRabbitModel):
    """Metadata about the comment analysis process.

    Contains information about the pull request, processing time,
    and statistics about the comments found.
    """

    pr_number: int
    pr_title: str
    owner: str
    repo: str
    processed_at: datetime
    total_comments: int
    coderabbit_comments: int
    resolved_comments: int
    actionable_comments: int
    processing_time_seconds: float
    # Detailed comment type statistics
    summary_comments: int = 0
    review_comments: int = 0
    nitpick_comments: int = 0
    outside_diff_comments: int = 0
    additional_comments: int = 0
    thread_contexts: int = 0
    adjusted_counts: Optional[Dict[str, int]] = None

    def __init__(self, **data) -> None:
        """Initialize metadata with current timestamp if not provided."""
        if "processed_at" not in data:
            data["processed_at"] = datetime.now()
        super().__init__(**data)

    @property
    def resolution_rate(self) -> float:
        """Calculate the resolution rate of CodeRabbit comments.

        Returns:
            Percentage of resolved comments (0.0 to 1.0)
        """
        if self.coderabbit_comments == 0:
            return 0.0
        return self.resolved_comments / self.coderabbit_comments

    @property
    def actionable_rate(self) -> float:
        """Calculate the rate of actionable comments.

        Returns:
            Percentage of actionable comments (0.0 to 1.0)
        """
        if self.coderabbit_comments == 0:
            return 0.0
        return self.actionable_comments / self.coderabbit_comments

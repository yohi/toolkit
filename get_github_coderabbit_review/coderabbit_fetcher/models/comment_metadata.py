"""
Metadata for comment analysis results.
"""

from datetime import datetime, timezone
from typing import Dict, List

from pydantic import Field
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
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_comments: int
    coderabbit_comments: int
    resolved_comments: int
    actionable_comments: int
    processing_time_seconds: float
    
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

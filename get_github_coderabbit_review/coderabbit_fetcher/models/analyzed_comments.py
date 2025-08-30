"""
Main analyzed comments data model.
"""

from typing import List

from pydantic import Field
from .base import BaseCodeRabbitModel
from .comment_metadata import CommentMetadata
from .summary_comment import SummaryComment
from .review_comment import ReviewComment
from .thread_context import ThreadContext


class AnalyzedComments(BaseCodeRabbitModel):
    """Complete analysis result of CodeRabbit comments.
    
    This is the main data structure that contains all analyzed
    information from a pull request's CodeRabbit comments.
    """
    
    summary_comments: List[SummaryComment] = Field(default_factory=list)
    review_comments: List[ReviewComment] = Field(default_factory=list)
    unresolved_threads: List[ThreadContext] = Field(default_factory=list)
    metadata: CommentMetadata
    
    @property
    def has_summary(self) -> bool:
        """Check if analysis contains summary comments.
        
        Returns:
            True if summary comments are present
        """
        return len(self.summary_comments) > 0
    
    @property
    def has_actionable_items(self) -> bool:
        """Check if analysis contains actionable items.
        
        Returns:
            True if any review comments have actionable items
        """
        return any(
            review.actionable_count > 0 
            for review in self.review_comments
        )
    
    @property
    def total_actionable_items(self) -> int:
        """Get total number of actionable items.
        
        Returns:
            Sum of all actionable items across reviews
        """
        return sum(
            review.actionable_count 
            for review in self.review_comments
        )
    
    @property
    def has_high_priority_issues(self) -> bool:
        """Check if analysis contains high priority issues.
        
        Returns:
            True if any review has high priority issues
        """
        return any(
            review.has_high_priority_issues
            for review in self.review_comments
        )
    
    @property
    def has_ai_prompts(self) -> bool:
        """Check if analysis contains AI agent prompts.
        
        Returns:
            True if any review has AI prompts
        """
        return any(
            review.has_ai_prompts
            for review in self.review_comments
        )
    
    @property
    def files_with_issues(self) -> List[str]:
        """Get list of files that have actionable comments.
        
        Returns:
            List of unique file paths with issues
        """
        files = set()
        
        for review in self.review_comments:
            for comment in review.actionable_comments:
                files.add(comment.file_path)
        
        return sorted(list(files))
    
    def get_summary_text(self) -> str:
        """Get a brief text summary of the analysis.
        
        Returns:
            Human-readable summary text
        """
        summary_parts = []
        
        if self.has_summary:
            summary_parts.append(f"{len(self.summary_comments)} summary comment(s)")
        
        if self.has_actionable_items:
            summary_parts.append(f"{self.total_actionable_items} actionable item(s)")
        
        if self.has_high_priority_issues:
            summary_parts.append("high priority issues found")
        
        if self.has_ai_prompts:
            summary_parts.append("AI prompts available")
        
        if not summary_parts:
            return "No significant CodeRabbit feedback found"
        
        return " | ".join(summary_parts)

"""
Review comment data model.
"""

from typing import List

from .base import BaseCodeRabbitModel
from .actionable_comment import ActionableComment


class NitpickComment(BaseCodeRabbitModel):
    """Nitpick comment from CodeRabbit.
    
    Represents minor style or formatting suggestions
    that don't affect functionality.
    """
    
    file_path: str
    line_range: str
    suggestion: str
    raw_content: str


class OutsideDiffComment(BaseCodeRabbitModel):
    """Comment outside the diff range.
    
    Represents comments that refer to code outside
    the current pull request diff.
    """
    
    file_path: str
    line_range: str
    content: str
    reason: str = "Outside diff range"
    raw_content: str


class ReviewComment(BaseCodeRabbitModel):
    """Review comment from CodeRabbit.
    
    Represents the main review comment that contains
    actionable feedback and suggestions.
    """
    
    actionable_count: int
    actionable_comments: List[ActionableComment] = []
    nitpick_comments: List[NitpickComment] = []
    outside_diff_comments: List[OutsideDiffComment] = []
    raw_content: str
    
    @property
    def total_issues(self) -> int:
        """Get total number of issues across all categories.
        
        Returns:
            Total count of all types of comments
        """
        return (
            len(self.actionable_comments) +
            len(self.nitpick_comments) +
            len(self.outside_diff_comments)
        )
    
    @property
    def has_high_priority_issues(self) -> bool:
        """Check if review contains high priority issues.
        
        Returns:
            True if any actionable comment has high priority
        """
        return any(
            comment.is_high_priority 
            for comment in self.actionable_comments
        )
    
    @property
    def has_ai_prompts(self) -> bool:
        """Check if review contains AI agent prompts.
        
        Returns:
            True if any actionable comment has AI prompts
        """
        return any(
            comment.has_ai_prompt
            for comment in self.actionable_comments
        )
    
    def get_comments_by_file(self, file_path: str) -> List[ActionableComment]:
        """Get all actionable comments for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of actionable comments for the file
        """
        return [
            comment for comment in self.actionable_comments
            if comment.file_path == file_path
        ]
    
    def get_high_priority_comments(self) -> List[ActionableComment]:
        """Get all high priority actionable comments.
        
        Returns:
            List of high priority comments
        """
        return [
            comment for comment in self.actionable_comments
            if comment.is_high_priority
        ]

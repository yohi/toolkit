"""Review comment data models."""

from typing import List

from pydantic import BaseModel, Field, model_validator
from .actionable_comment import ActionableComment
from .ai_agent_prompt import AIAgentPrompt


class BasicReviewComment(BaseModel):
    """Basic review comment model for simple use cases."""
    
    actionable_count: int = Field(..., description="Number of actionable comments")
    raw_content: str = Field(..., description="Original comment content")


class NitpickComment(BaseModel):
    """Represents a nitpick comment for minor code style suggestions."""
    
    file_path: str = Field(..., description="Path to the file being commented on")
    line_range: str = Field(..., description="Line number or range")
    suggestion: str = Field(..., description="The nitpick suggestion")
    raw_content: str = Field(..., description="Original comment content")


class OutsideDiffComment(BaseModel):
    """Represents a comment that refers to code outside the diff range."""
    
    file_path: str = Field(..., description="Path to the file being commented on")
    line_range: str = Field(..., description="Line number or range")
    content: str = Field(..., description="Comment content")
    reason: str = Field(..., description="Reason why this is outside diff")
    raw_content: str = Field(..., description="Original comment content")


class ReviewComment(BaseModel):
    """Represents a processed CodeRabbit review comment."""
    
    actionable_count: int
    actionable_comments: List[ActionableComment] = Field(default_factory=list)
    nitpick_comments: List[NitpickComment] = Field(default_factory=list)
    outside_diff_comments: List[OutsideDiffComment] = Field(default_factory=list)
    ai_agent_prompts: List[AIAgentPrompt] = Field(default_factory=list)
    raw_content: str
    
    @model_validator(mode="after")
    def sync_actionable_count(self):
        """If no reported count, fall back to parsed length."""
        if self.actionable_count == 0:
            self.actionable_count = len(self.actionable_comments)
        return self
    
    @property
    def total_issues(self) -> int:
        """Get total number of issues across all categories."""
        return (
            len(self.actionable_comments) +
            len(self.nitpick_comments) +
            len(self.outside_diff_comments)
        )
    
    def __str__(self) -> str:
        """String representation of the review comment."""
        return f"ReviewComment(actionable={self.actionable_count}, nitpick={len(self.nitpick_comments)}, outside_diff={len(self.outside_diff_comments)})"

# Backward compatibility alias for simpler review comments
SimpleReviewComment = BasicReviewComment
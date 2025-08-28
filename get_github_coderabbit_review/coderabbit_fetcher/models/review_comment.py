"""Review comment data models."""

from pydantic import BaseModel, Field
from typing import List, Optional
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

    actionable_count: int = Field(..., description="Number of actionable comments")
    actionable_comments: List[ActionableComment] = Field(
        default_factory=list,
        description="List of actionable comments"
    )
    nitpick_comments: List[NitpickComment] = Field(
        default_factory=list,
        description="List of nitpick comments"
    )
    outside_diff_comments: List[OutsideDiffComment] = Field(
        default_factory=list,
        description="List of outside diff comments"
    )
    ai_agent_prompts: List[AIAgentPrompt] = Field(
        default_factory=list,
        description="List of AI agent prompts"
    )
    raw_content: str = Field(..., description="Original comment content")

    def __str__(self) -> str:
        """String representation of the review comment."""
        return f"ReviewComment(actionable={self.actionable_count}, nitpick={len(self.nitpick_comments)}, outside_diff={len(self.outside_diff_comments)})"
    
    @property
    def has_ai_prompts(self) -> bool:
        """Check if this review comment has AI agent prompts.
        
        Returns:
            True if there are AI agent prompts
        """
        return len(self.ai_agent_prompts) > 0


# Backward compatibility alias for simpler review comments
SimpleReviewComment = BasicReviewComment

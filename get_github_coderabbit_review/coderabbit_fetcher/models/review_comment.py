"""Review comment data models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from .actionable_comment import ActionableComment
from .ai_agent_prompt import AIAgentPrompt


class BasicReviewComment(BaseModel):
    """Basic review comment model for simple use cases."""

    actionable_count: int = Field(..., description="Number of actionable comments")
    raw_content: str = Field(..., description="Original comment content")

    @property
    def line_number(self) -> Optional[str]:
        """BasicReviewComment doesn't have line information."""
        return None

    @property 
    def title(self) -> str:
        """Generate a title for basic review comment."""
        return f"Review Comment ({self.actionable_count} actionable items)"

    @property
    def issue(self) -> str:
        """Return the main issue/content for this comment."""
        return f"Review with {self.actionable_count} actionable items"

    @property
    def issue_description(self) -> str:
        """Return issue description for compatibility."""
        return f"Review with {self.actionable_count} actionable items"


class NitpickComment(BaseModel):
    """Represents a nitpick comment for minor code style suggestions."""

    file_path: str = Field(..., description="Path to the file being commented on")
    line_range: str = Field(..., description="Line number or range")
    suggestion: str = Field(..., description="The nitpick suggestion")
    raw_content: str = Field(..., description="Original comment content")

    @property
    def line_number(self) -> Optional[str]:
        """Extract line number from line_range."""
        if not self.line_range:
            return None
        
        if '-' in self.line_range:
            return self.line_range.split('-')[0].strip()
        else:
            return self.line_range.strip()

    @property 
    def title(self) -> str:
        """Generate a title from suggestion."""
        if not self.suggestion:
            return "Nitpick Comment"
        
        first_sentence = self.suggestion.split('.')[0].strip()
        if len(first_sentence) > 80:
            return first_sentence[:77] + "..."
        return first_sentence if first_sentence else "Nitpick Comment"

    @property
    def issue(self) -> str:
        """Return the main issue/content for this comment."""
        return self.suggestion

    @property
    def issue_description(self) -> str:
        """Return issue description for compatibility."""
        return self.suggestion


class OutsideDiffComment(BaseModel):
    """Represents a comment that refers to code outside the diff range."""

    file_path: str = Field(..., description="Path to the file being commented on")
    line_range: str = Field(..., description="Line number or range")
    content: str = Field(..., description="Comment content")
    reason: str = Field(..., description="Reason why this is outside diff")
    raw_content: str = Field(..., description="Original comment content")

    @property
    def line_number(self) -> Optional[str]:
        """Extract line number from line_range."""
        if not self.line_range:
            return None
        
        if '-' in self.line_range:
            return self.line_range.split('-')[0].strip()
        else:
            return self.line_range.strip()

    @property 
    def title(self) -> str:
        """Generate a title from content."""
        if not self.content:
            return "Outside Diff Comment"
        
        first_sentence = self.content.split('.')[0].strip()
        if len(first_sentence) > 80:
            return first_sentence[:77] + "..."
        return first_sentence if first_sentence else "Outside Diff Comment"

    @property
    def issue(self) -> str:
        """Return the main issue/content for this comment."""
        return self.content

    @property
    def issue_description(self) -> str:
        """Return issue description for compatibility."""
        return self.content


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

    @property
    def line_number(self) -> Optional[str]:
        """ReviewComment doesn't have line information directly."""
        return None

    @property 
    def title(self) -> str:
        """Generate a title for review comment."""
        total_comments = len(self.nitpick_comments) + len(self.outside_diff_comments)
        if self.has_ai_prompts:
            return f"Review with AI Prompts ({self.actionable_count} actionable, {total_comments} other)"
        else:
            return f"Review Comment ({self.actionable_count} actionable, {total_comments} other)"

    @property
    def issue(self) -> str:
        """Return the main issue/content for this comment."""
        total_comments = len(self.nitpick_comments) + len(self.outside_diff_comments)
        return f"Review with {self.actionable_count} actionable comments and {total_comments} other comments"

    @property
    def issue_description(self) -> str:
        """Return issue description for compatibility."""
        total_comments = len(self.nitpick_comments) + len(self.outside_diff_comments)
        return f"Review with {self.actionable_count} actionable comments and {total_comments} other comments"


# Backward compatibility alias for simpler review comments
SimpleReviewComment = BasicReviewComment

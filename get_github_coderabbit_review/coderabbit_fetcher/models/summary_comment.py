"""
Summary comment data model.
"""

from typing import List, Optional

from .base import BaseCodeRabbitModel


class ChangeEntry(BaseCodeRabbitModel):
    """Entry in the changes table from CodeRabbit summary.

    Represents a single row in the changes table that
    CodeRabbit generates in summary comments.
    """

    cohort_or_files: str
    summary: str

    def __str__(self) -> str:
        """String representation of change entry."""
        return f"{self.cohort_or_files}: {self.summary}"


class SummaryComment(BaseCodeRabbitModel):
    """Summary comment from CodeRabbit.

    Represents the "Summary by CodeRabbit" comment that provides
    an overview of changes in the pull request.
    """

    new_features: List[str] = []
    documentation_changes: List[str] = []
    test_changes: List[str] = []
    walkthrough: str = ""
    changes_table: List[ChangeEntry] = []
    sequence_diagram: Optional[str] = None
    raw_content: str

    @property
    def has_new_features(self) -> bool:
        """Check if summary contains new features.

        Returns:
            True if new features are mentioned
        """
        return len(self.new_features) > 0

    @property
    def has_documentation_changes(self) -> bool:
        """Check if summary contains documentation changes.

        Returns:
            True if documentation changes are mentioned
        """
        return len(self.documentation_changes) > 0

    @property
    def has_test_changes(self) -> bool:
        """Check if summary contains test changes.

        Returns:
            True if test changes are mentioned
        """
        return len(self.test_changes) > 0

    @property
    def has_sequence_diagram(self) -> bool:
        """Check if summary contains sequence diagram.

        Returns:
            True if sequence diagram is present
        """
        return self.sequence_diagram is not None

    @property
    def total_changes(self) -> int:
        """Get total number of changes across all categories.

        Returns:
            Total count of changes mentioned
        """
        return (
            len(self.new_features) +
            len(self.documentation_changes) +
            len(self.test_changes) +
            len(self.changes_table)
        )

    def get_formatted_walkthrough(self, max_length: int = 500) -> str:
        """Get formatted walkthrough with optional truncation.

        Args:
            max_length: Maximum length of walkthrough text

        Returns:
            Formatted walkthrough text
        """
        if not self.walkthrough:
            return "No walkthrough provided."

        if len(self.walkthrough) <= max_length:
            return self.walkthrough

        return self.walkthrough[:max_length - 3] + "..."

"""
Base formatter interface for CodeRabbit Comment Fetcher.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Formatter(ABC):
    """Base formatter interface for output formatting."""

    @abstractmethod
    def format(self, persona: str, analyzed_comments: Dict[str, Any]) -> str:
        """Format the analyzed comments with the given persona.

        Args:
            persona: The persona context for formatting
            analyzed_comments: The analyzed comments data

        Returns:
            Formatted string output
        """
        pass

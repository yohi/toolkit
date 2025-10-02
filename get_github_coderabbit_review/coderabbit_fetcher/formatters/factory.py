"""
Factory for creating formatter instances.
"""

from typing import Dict, Type

from ..exceptions import CodeRabbitFetcherError
from .base import Formatter
from .json_formatter import JsonFormatter
from .markdown import MarkdownFormatter
from .plain import PlainFormatter


class FormatterFactory:
    """Factory for creating output formatters."""

    def __init__(self):
        """Initialize the formatter factory with available formatters."""
        self._formatters: Dict[str, Type[Formatter]] = {
            "markdown": MarkdownFormatter,
            "json": JsonFormatter,
            "plain": PlainFormatter,
        }

    def create_formatter(self, output_format: str) -> Formatter:
        """Create a formatter instance for the given format.

        Args:
            output_format: The desired output format (case-insensitive)

        Returns:
            Formatter instance for the specified format

        Raises:
            CodeRabbitFetcherError: If the output format is not supported
        """
        # Normalize the format string (case-insensitive)
        normalized_format = output_format.lower().strip()

        if normalized_format not in self._formatters:
            supported_formats = ", ".join(self._formatters.keys())
            raise CodeRabbitFetcherError(
                f"Unsupported output format: '{output_format}'. "
                f"Supported formats: {supported_formats}"
            )

        formatter_class = self._formatters[normalized_format]
        return formatter_class()

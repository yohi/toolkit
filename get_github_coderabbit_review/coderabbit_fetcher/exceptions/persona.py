"""Persona-related exceptions."""

from typing import Optional

from .base import CodeRabbitFetcherError


class PersonaFileError(CodeRabbitFetcherError):
    """Base exception for persona file-related errors."""

    pass


class PersonaLoadError(PersonaFileError):
    """Exception raised when persona loading fails."""

    def __init__(self, message: str, file_path: Optional[str] = None):
        """Initialize persona load error.

        Args:
            message: Error message
            file_path: Optional file path that caused the error
        """
        self.file_path = file_path
        super().__init__(message)

    def __str__(self) -> str:
        """String representation of the error."""
        if self.file_path:
            return f"PersonaLoadError in {self.file_path}: {super().__str__()}"
        return f"PersonaLoadError: {super().__str__()}"


class PersonaValidationError(PersonaLoadError):
    """Exception raised when persona content validation fails."""

    def __init__(
        self, message: str, file_path: Optional[str] = None, validation_rule: Optional[str] = None
    ):
        """Initialize persona validation error.

        Args:
            message: Error message
            file_path: Optional file path that caused the error
            validation_rule: Optional validation rule that failed
        """
        self.validation_rule = validation_rule
        super().__init__(message, file_path)

    def __str__(self) -> str:
        """String representation of the error."""
        base_str = super().__str__()
        if self.validation_rule:
            return f"{base_str} (Rule: {self.validation_rule})"
        return base_str

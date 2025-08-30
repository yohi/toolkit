"""
Persona file related exceptions.
"""

from .base import CodeRabbitFetcherError


class PersonaFileError(CodeRabbitFetcherError):
    """Persona file reading issues.
    
    Raised when a persona file cannot be read or contains
    invalid content.
    """
    
    def __init__(self, message: str, file_path: str | None = None) -> None:
        """Initialize the persona file error.
        
        Args:
            message: Error message describing the issue
            file_path: Optional path to the problematic file
        """
        details = None
        if file_path is not None:
            details = f"File path: {file_path}"
        
        super().__init__(message, details)

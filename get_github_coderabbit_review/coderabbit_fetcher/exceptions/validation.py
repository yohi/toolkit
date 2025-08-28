"""Validation-related exceptions."""

from typing import Optional, List, Dict, Any
from .base import CodeRabbitFetcherError


class ValidationError(CodeRabbitFetcherError):
    """Exception raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if validation_errors:
            details['validation_errors'] = validation_errors

        suggestions = kwargs.get('suggestions', [
            "Check input parameters and values",
            "Refer to help documentation",
            "Use --help for usage information"
        ])

        super().__init__(
            message,
            details=details,
            suggestions=suggestions,
            **kwargs
        )


class ConfigurationValidationError(ValidationError):
    """Exception raised when configuration validation fails."""

    def __init__(self, message: str, config_section: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if config_section:
            details['config_section'] = config_section

        super().__init__(
            message,
            suggestions=[
                "Check configuration syntax and values",
                "Verify all required parameters are provided",
                "Review configuration documentation"
            ],
            **kwargs
        )


class URLValidationError(ValidationError):
    """Exception raised when URL validation fails."""

    def __init__(self, message: str, url: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if url:
            details['provided_url'] = url

        super().__init__(
            message,
            field="url",
            suggestions=[
                "Use format: https://github.com/owner/repo/pull/123",
                "Ensure the URL is complete and correct",
                "Check for typos in the owner/repository names"
            ],
            **kwargs
        )


class FileValidationError(ValidationError):
    """Exception raised when file validation fails."""

    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if file_path:
            details['file_path'] = file_path

        super().__init__(
            message,
            field="file_path",
            suggestions=[
                "Check if the file exists and is readable",
                "Verify file permissions",
                "Ensure the file path is correct"
            ],
            **kwargs
        )


class ParameterValidationError(ValidationError):
    """Exception raised when parameter validation fails."""

    def __init__(
        self,
        message: str,
        parameter: Optional[str] = None,
        expected_type: Optional[str] = None,
        provided_value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if parameter:
            details['parameter'] = parameter
        if expected_type:
            details['expected_type'] = expected_type
        if provided_value is not None:
            details['provided_value'] = str(provided_value)

        super().__init__(
            message,
            field=parameter,
            suggestions=[
                f"Provide a valid {expected_type}" if expected_type else "Check parameter format",
                "Refer to documentation for valid values",
                "Use --help for parameter information"
            ],
            **kwargs
        )

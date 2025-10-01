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
        **kwargs,
    ):
        details = dict(kwargs.pop("details", {}) or {})
        if field:
            details["field"] = field
        if validation_errors:
            details["validation_errors"] = validation_errors

        suggestions = kwargs.pop(
            "suggestions",
            [
                "Check input parameters and values",
                "Refer to help documentation",
                "Use --help for usage information",
            ],
        )

        super().__init__(message, details=details, suggestions=suggestions, **kwargs)


class ConfigurationValidationError(ValidationError):
    """Exception raised when configuration validation fails."""

    def __init__(self, message: str, config_section: Optional[str] = None, **kwargs):
        details = dict(kwargs.pop("details", {}) or {})
        if config_section:
            details["config_section"] = config_section

        suggestions = kwargs.pop(
            "suggestions",
            [
                "Check configuration syntax and values",
                "Verify all required parameters are provided",
                "Review configuration documentation",
            ],
        )

        super().__init__(message, details=details, suggestions=suggestions, **kwargs)


class URLValidationError(ValidationError):
    """Exception raised when URL validation fails."""

    def __init__(self, message: str, url: Optional[str] = None, **kwargs):
        details = dict(kwargs.pop("details", {}) or {})
        if url:
            details["provided_url"] = url

        suggestions = kwargs.pop(
            "suggestions",
            [
                "Use format: https://github.com/owner/repo/pull/123",
                "Ensure the URL is complete and correct",
                "Check for typos in the owner/repository names",
            ],
        )

        super().__init__(message, field="url", details=details, suggestions=suggestions, **kwargs)


class FileValidationError(ValidationError):
    """Exception raised when file validation fails."""

    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        details = dict(kwargs.pop("details", {}) or {})
        if file_path:
            details["file_path"] = file_path

        suggestions = kwargs.pop(
            "suggestions",
            [
                "Check if the file exists and is readable",
                "Verify file permissions",
                "Ensure the file path is correct",
            ],
        )

        super().__init__(
            message, field="file_path", details=details, suggestions=suggestions, **kwargs
        )


class ParameterValidationError(ValidationError):
    """Exception raised when parameter validation fails."""

    def __init__(
        self,
        message: str,
        parameter: Optional[str] = None,
        expected_type: Optional[str] = None,
        provided_value: Optional[Any] = None,
        **kwargs,
    ):
        details = dict(kwargs.pop("details", {}) or {})
        if parameter:
            details["parameter"] = parameter
        if expected_type:
            details["expected_type"] = expected_type
        if provided_value is not None:
            details["provided_value"] = str(provided_value)

        suggestions = kwargs.pop(
            "suggestions",
            [
                f"Provide a valid {expected_type}" if expected_type else "Check parameter format",
                "Refer to documentation for valid values",
                "Use --help for parameter information",
            ],
        )

        super().__init__(
            message, field=parameter, details=details, suggestions=suggestions, **kwargs
        )

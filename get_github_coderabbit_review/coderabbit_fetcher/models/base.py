"""
Base classes for data models.
"""

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class BaseCodeRabbitModel(BaseModel):
    """Base model for all CodeRabbit data structures.

    Provides common configuration and utility methods for all models
    in the application.
    """

    model_config = ConfigDict(
        # Enable validation on assignment
        validate_assignment=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Allow extra fields for future compatibility
        extra="forbid",
        # Validate default values
        validate_default=True,
        # String handling
        str_strip_whitespace=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return self.model_dump()

    def to_json(self) -> str:
        """Convert model to JSON string.

        Returns:
            JSON string representation of the model
        """
        return self.model_dump_json(indent=2)

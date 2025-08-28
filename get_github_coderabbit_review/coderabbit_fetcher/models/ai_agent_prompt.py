"""
AI Agent prompt data model.
"""

from typing import Optional

from .base import BaseCodeRabbitModel


class AIAgentPrompt(BaseCodeRabbitModel):
    """AI agent prompt extracted from CodeRabbit comments.

    Represents code suggestions or prompts specifically marked
    for AI agent consumption in CodeRabbit comments.
    """

    code_block: str
    language: Optional[str] = None
    description: str
    suggested_action: Optional[str] = None
    file_path: Optional[str] = None
    line_range: Optional[str] = None

    def __init__(self, **data) -> None:
        """Initialize AI agent prompt."""
        # Auto-detect language from code block if not provided
        if "language" not in data or not data["language"]:
            data["language"] = self._detect_language(data.get("code_block", ""))
        super().__init__(**data)

    @staticmethod
    def _detect_language(code_block: str) -> Optional[str]:
        """Detect programming language from code block.

        Args:
            code_block: Code content to analyze

        Returns:
            Detected language or None if uncertain
        """
        code = code_block.strip().lower()

        # Simple heuristics for language detection
        if any(keyword in code for keyword in ["def ", "import ", "class ", "if __name__"]):
            return "python"
        elif any(keyword in code for keyword in ["function ", "const ", "let ", "var "]):
            return "javascript"
        elif any(keyword in code for keyword in ["public class", "private ", "import java"]):
            return "java"
        elif any(keyword in code for keyword in ["#include", "int main", "std::"]):
            return "cpp"
        elif any(keyword in code for keyword in ["func ", "package ", "import \""]):
            return "go"

        return None

    @property
    def is_complete_suggestion(self) -> bool:
        """Check if this is a complete code suggestion.

        Returns:
            True if prompt contains complete implementation suggestion
        """
        return (
            self.code_block and
            len(self.code_block.strip()) > 50 and
            self.language is not None
        )

"""
Formatters package for CodeRabbit Comment Fetcher.

This package provides various output formatters for processing and displaying
CodeRabbit comments in different formats.
"""

from .ai_agent_prompt_formatter import AIAgentPromptFormatter
from .base_formatter import BaseFormatter
from .json_formatter import JSONFormatter
from .llm_instruction_formatter import LLMInstructionFormatter
from .markdown_formatter import MarkdownFormatter
from .plaintext_formatter import PlainTextFormatter

__version__ = "1.0.0"

__all__ = [
    "BaseFormatter",
    "MarkdownFormatter",
    "JSONFormatter",
    "PlainTextFormatter",
    "LLMInstructionFormatter",
    "AIAgentPromptFormatter",
]

"""
Markdown formatter for CodeRabbit Comment Fetcher.
"""

import json
from typing import Any, Dict

from .base import Formatter


class MarkdownFormatter(Formatter):
    """Markdown output formatter."""
    
    def format(self, persona: str, analyzed_comments: Dict[str, Any]) -> str:
        """Format the analyzed comments as Markdown.
        
        Args:
            persona: The persona context for formatting
            analyzed_comments: The analyzed comments data
            
        Returns:
            Formatted Markdown string
        """
        lines = []
        
        # Title
        lines.append("# CodeRabbit Comments Analysis")
        lines.append("")
        
        # Persona context if provided
        if persona and persona.strip():
            lines.append("## Context")
            lines.append(persona)
            lines.append("")
        
        # Summary
        metadata = analyzed_comments.get('metadata', {})
        lines.append("## Summary")
        lines.append(f"- **Pull Request**: #{metadata.get('pull_request_number', 'N/A')}")
        lines.append(f"- **Total Comments**: {metadata.get('total_inline_comments', 0)}")
        lines.append(f"- **Total Reviews**: {metadata.get('total_reviews', 0)}")
        lines.append("")
        
        # Comments
        inline_comments = analyzed_comments.get('inline_comments', [])
        if inline_comments:
            lines.append("## Inline Comments")
            for i, comment in enumerate(inline_comments, 1):
                lines.append(f"### Comment {i}")
                lines.append(f"**File**: `{comment.get('path', 'N/A')}`")
                lines.append(f"**User**: {comment.get('user', 'N/A')}")
                if comment.get('is_coderabbit'):
                    lines.append("**Source**: CodeRabbit 🤖")
                lines.append("")
                body = comment.get('body', '')
                if body:
                    lines.append(body)
                lines.append("")
        
        return "\n".join(lines)
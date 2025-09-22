"""
Utility functions for extracting diff blocks from CodeRabbit comments.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DiffExtractor:
    """Utility class for extracting various types of diff blocks from comment content."""

    @staticmethod
    def extract_diff_blocks(content: str) -> str:
        """Extract diff blocks from comment content.

        Args:
            content: Raw comment content

        Returns:
            Extracted diff block or empty string
        """
        if not content:
            return ""

        # Look for diff blocks between ```diff and ``` markers
        diff_pattern = r"```diff\s*\n(.*?)\n```"
        matches = re.findall(diff_pattern, content, re.DOTALL)

        if matches:
            # Use the first diff block found
            diff_content = matches[0].strip()
            if diff_content:
                logger.debug(f"Found diff block: {len(diff_content)} chars")
                return f"```diff\n{diff_content}\n```"

        # If no diff blocks, look for suggestion blocks
        suggestion_pattern = r"```suggestion\s*\n(.*?)\n```"
        suggestion_matches = re.findall(suggestion_pattern, content, re.DOTALL)

        if suggestion_matches:
            suggestion_content = suggestion_matches[0].strip()
            if suggestion_content:
                logger.debug(f"Found suggestion block: {len(suggestion_content)} chars")
                return f"```diff\n{suggestion_content}\n```"

        # Look for code blocks with + or - prefixes (inline diff style)
        inline_diff_pattern = r"```[\w]*\n([^`]*(?:[+-][^\n]*\n)+[^`]*)\n```"
        inline_matches = re.findall(inline_diff_pattern, content, re.DOTALL)

        if inline_matches:
            inline_content = inline_matches[0].strip()
            if inline_content and ("+" in inline_content or "-" in inline_content):
                logger.debug(f"Found inline diff: {len(inline_content)} chars")
                return f"```diff\n{inline_content}\n```"

        # Look for generic code blocks that might contain diffs
        code_block_pattern = r"```[\w]*\n(.*?)\n```"
        code_matches = re.findall(code_block_pattern, content, re.DOTALL)

        for code_match in code_matches:
            code_content = code_match.strip()
            # Check if it looks like a diff (has + or - at line starts)
            lines = code_content.split("\n")
            diff_lines = [line for line in lines if line.strip().startswith(("+", "-"))]

            if diff_lines and len(diff_lines) >= 2:  # At least 2 diff lines
                logger.debug(f"Found code block with diff patterns: {len(code_content)} chars")
                return f"```diff\n{code_content}\n```"

        logger.debug("No diff content found")
        return ""

    @staticmethod
    def extract_all_code_blocks(content: str) -> List[Dict[str, Any]]:
        """Extract all code blocks from content with enhanced detection.

        Args:
            content: Text content that may contain code blocks

        Returns:
            List of dictionaries containing code block info: {code, language, type}
        """
        code_blocks = []

        if not content:
            return code_blocks

        # Enhanced code block patterns
        patterns = [
            # Multi-line diff blocks
            (r"```diff\s*\n(.*?)\n```", "diff", "diff"),
            # Standard markdown code blocks with language
            (r"```(\w+)\s*\n(.*?)\n```", r"\1", "code_block"),
            # Standard markdown code blocks without language
            (r"```\s*\n(.*?)\n```", "text", "code_block"),
            # Multi-line code suggestions (+ prefix)
            (r"(\n\+[^\n]*(?:\n\+[^\n]*)*)", "diff", "suggestion"),
            # Inline code (only if meaningful - more than just a word)
            (r"`([^`\n]{10,})`", "text", "inline"),
            # HTML code tags
            (r"<code>(.*?)</code>", "text", "html_code"),
        ]

        for pattern, language_or_group, block_type in patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if block_type == "suggestion":
                    # Handle diff-style suggestions
                    code_content = match.group(1).strip()
                    # Clean up the + prefixes and reconstruct the code
                    lines = []
                    for line in code_content.split("\n"):
                        if line.startswith("+"):
                            lines.append(line[1:].strip())
                    code_content = "\n".join(lines)
                    language = "diff"
                else:
                    code_content = match.group(2 if r"\1" in language_or_group else 1).strip()
                    language = match.group(1) if r"\1" in language_or_group else language_or_group

                # Filter out meaningless code fragments
                if code_content and len(code_content) > 10:
                    # Skip fragments that are just variable names or simple expressions
                    if not re.match(r"^[\w\s]*$", code_content) or " " in code_content:
                        code_blocks.append(
                            {"code": code_content, "language": language, "type": block_type}
                        )

        return code_blocks

    @staticmethod
    def extract_title_from_content(content: str) -> str:
        """Extract title from comment content.

        Args:
            content: Raw comment content

        Returns:
            Extracted title or default title
        """
        if not content:
            return "CodeRabbit Comment"

        # Look for bold text patterns that typically indicate titles
        title_patterns = [
            r"\*\*([^*]+)\*\*",  # **Bold text**
            r"__([^_]+)__",  # __Bold text__
            r"^([^.\n]+)",  # First line without period
        ]

        for pattern in title_patterns:
            match = re.search(pattern, content.strip(), re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if title and len(title) > 3:  # Meaningful title
                    # Truncate if too long
                    if len(title) > 80:
                        title = title[:77] + "..."
                    return title

        return "CodeRabbit Comment"

    @staticmethod
    def extract_description_from_content(content: str) -> str:
        """Extract description from comment content.

        Args:
            content: Raw comment content

        Returns:
            Extracted description
        """
        if not content:
            return ""

        # Remove title (first bold text) and extract description
        content_without_title = re.sub(
            r"^\*\*[^*]+\*\*\s*", "", content.strip(), flags=re.MULTILINE
        )

        # Extract text before first code block or AI prompt
        description_match = re.search(
            r"^(.*?)(?:```|🤖 Prompt for AI Agents|\Z)",
            content_without_title,
            re.DOTALL | re.MULTILINE,
        )

        if description_match:
            description = description_match.group(1).strip()
            # Clean up extra whitespace and newlines
            description = re.sub(r"\n\s*\n", "\n\n", description)
            description = re.sub(r"^\s+|\s+$", "", description, flags=re.MULTILINE)

            if description:
                return description

        # Fallback: truncate original content
        fallback = content[:300] + "..." if len(content) > 300 else content
        return fallback.strip()

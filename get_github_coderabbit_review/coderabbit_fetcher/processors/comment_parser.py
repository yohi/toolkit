"""Comment parsing utilities for extracting structured content from CodeRabbit comments."""

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional

from ..models import ActionableComment, AIAgentPrompt
from ..models.review_comment import NitpickComment, OutsideDiffComment

logger = logging.getLogger(__name__)


class CommentParser:
    """Handles parsing and extraction of different comment types from CodeRabbit content."""

    def __init__(self):
        """Initialize the comment parser."""
        self.nitpick_patterns = [
            r"🧹 Nitpick comments?",
            r"Nitpick comments?",
            r"Minor suggestions?",
            r"Style suggestions?",
        ]

        self.outside_diff_patterns = [
            r"⚠️ Outside diff range comments?",
            r"Outside diff range comments?",
            r"Comments? outside the diff",
            r"Outside.*diff.*range",
        ]

        self.ai_agent_patterns = [
            r"🤖 Prompt for AI Agents",
            r"Prompt for AI Agents",
            r"AI Agent Prompt",
            r"For AI Agents",
        ]

    def extract_actionable_comments(self, content: str) -> List[ActionableComment]:
        """Extract actionable comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of ActionableComment objects
        """
        actionable_comments = []

        try:
            # Find sections containing actionable comments
            actionable_patterns = [
                r"## 🛠️ Refactor Suggestions?\s*\n(.*?)(?=\n## |\Z)",
                r"## ⚠️ Potential Issues?\s*\n(.*?)(?=\n## |\Z)",
                r"## 📝 Committable Suggestions?\s*\n(.*?)(?=\n## |\Z)",
            ]

            for pattern in actionable_patterns:
                matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    section_content = match.group(1)
                    comments = self._parse_actionable_section(section_content)
                    actionable_comments.extend(comments)

            return actionable_comments

        except Exception as e:
            logger.warning(f"Failed to extract actionable comments: {e}")
            return []

    def extract_nitpick_comments(self, content: str) -> List[NitpickComment]:
        """Extract nitpick comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of NitpickComment objects
        """
        nitpick_comments = []

        try:
            # Find nitpick sections
            for pattern in self.nitpick_patterns:
                matches = re.finditer(
                    rf"{pattern}\s*\n(.*?)(?=\n## |\n\Z)", content, re.DOTALL | re.IGNORECASE
                )

                for match in matches:
                    section_content = match.group(1)
                    comments = self._parse_nitpick_section(section_content)
                    nitpick_comments.extend(comments)

            return nitpick_comments

        except Exception as e:
            logger.warning(f"Failed to extract nitpick comments: {e}")
            return []

    def extract_outside_diff_comments(self, content: str) -> List[OutsideDiffComment]:
        """Extract outside diff range comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of OutsideDiffComment objects
        """
        outside_diff_comments = []

        try:
            for pattern in self.outside_diff_patterns:
                matches = re.finditer(
                    rf"{pattern}\s*\n(.*?)(?=\n## |\n\Z)", content, re.DOTALL | re.IGNORECASE
                )

                for match in matches:
                    section_content = match.group(1)
                    comments = self._parse_outside_diff_section(section_content)
                    outside_diff_comments.extend(comments)

            return outside_diff_comments

        except Exception as e:
            logger.warning(f"Failed to extract outside diff comments: {e}")
            return []

    def extract_ai_agent_prompts(self, content: str) -> List[AIAgentPrompt]:
        """Extract AI agent prompts from review content.

        Args:
            content: Review comment body

        Returns:
            List of AIAgentPrompt objects
        """
        ai_prompts = []

        try:
            for pattern in self.ai_agent_patterns:
                matches = re.finditer(
                    rf"{pattern}\s*\n(.*?)(?=\n## |\n\Z)", content, re.DOTALL | re.IGNORECASE
                )

                for match in matches:
                    section_content = match.group(1)
                    prompts = self._parse_ai_agent_section(section_content)
                    ai_prompts.extend(prompts)

            return ai_prompts

        except Exception as e:
            logger.warning(f"Failed to extract AI agent prompts: {e}")
            return []

    def _parse_actionable_section(self, section_content: str) -> List[ActionableComment]:
        """Parse actionable comment section content."""
        comments = []

        # Split by common delimiters for individual comments
        comment_blocks = re.split(r"\n\n(?=\*\*|\d+\.)", section_content)

        for block in comment_blocks:
            if block.strip():
                comment = self._create_actionable_comment(block)
                if comment:
                    comments.append(comment)

        return comments

    def _parse_nitpick_section(self, section_content: str) -> List[NitpickComment]:
        """Parse nitpick comment section content."""
        comments = []

        # Split by bullet points or numbered items
        comment_blocks = re.split(r"\n(?=\*|-|\d+\.)", section_content)

        for block in comment_blocks:
            if block.strip():
                comment = self._create_nitpick_comment(block)
                if comment:
                    comments.append(comment)

        return comments

    def _parse_outside_diff_section(self, section_content: str) -> List[OutsideDiffComment]:
        """Parse outside diff comment section content."""
        comments = []

        # Split by file references or bullet points
        comment_blocks = re.split(r"\n(?=\*|-|\d+\.|\w+\.\w+:)", section_content)

        for block in comment_blocks:
            if block.strip():
                comment = self._create_outside_diff_comment(block)
                if comment:
                    comments.append(comment)

        return comments

    def _parse_ai_agent_section(self, section_content: str) -> List[AIAgentPrompt]:
        """Parse AI agent prompt section content."""
        prompts = []

        # AI agent prompts are usually in code blocks or details elements
        prompt_blocks = re.findall(r"```[\s\S]*?```|<details>[\s\S]*?</details>", section_content)

        for block in prompt_blocks:
            prompt = self._create_ai_agent_prompt(block)
            if prompt:
                prompts.append(prompt)

        return prompts

    def _create_actionable_comment(self, content: str) -> Optional[ActionableComment]:
        """Create ActionableComment object from content."""
        try:
            # Extract file path and line info
            file_info = self._extract_file_info(content)
            description = self._extract_description(content)
            suggestion = self._extract_suggestion(content)

            if description:
                comment_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                return ActionableComment(
                    comment_id=f"actionable_{comment_hash}",
                    issue_description=description,
                    proposed_diff=suggestion,
                    file_path=file_info.get("path", ""),
                    line_range=str(file_info.get("line", 0)),
                    raw_content=content,
                )
        except Exception as e:
            logger.debug(f"Failed to create actionable comment: {e}")

        return None

    def _create_nitpick_comment(self, content: str) -> Optional[NitpickComment]:
        """Create NitpickComment object from content."""
        try:
            file_info = self._extract_file_info(content)
            suggestion = self._extract_suggestion(content)

            if suggestion:
                return NitpickComment(
                    suggestion=suggestion,
                    file_path=file_info.get("path", ""),
                    line_range=str(file_info.get("line", 0)) if file_info.get("line") else file_info.get("line_range", ""),
                    raw_content=content,
                )
        except Exception as e:
            logger.debug(f"Failed to create nitpick comment: {e}")

        return None

    def _create_outside_diff_comment(self, content: str) -> Optional[OutsideDiffComment]:
        """Create OutsideDiffComment object from content."""
        try:
            file_info = self._extract_file_info(content)
            suggestion = self._extract_suggestion(content)
            description = self._extract_description(content)

            if suggestion or description:
                comment_content = suggestion or description or content.strip()
                return OutsideDiffComment(
                    content=comment_content,
                    reason="Comment refers to code outside the current diff range",
                    file_path=file_info.get("path", ""),
                    line_range=str(file_info.get("line", 0)) if file_info.get("line") else file_info.get("line_range", ""),
                    raw_content=content,
                )
        except Exception as e:
            logger.debug(f"Failed to create outside diff comment: {e}")

        return None

    def _create_ai_agent_prompt(self, content: str) -> Optional[AIAgentPrompt]:
        """Create AIAgentPrompt object from content."""
        try:
            # Extract code block from content
            code_block_match = re.search(r"```[\w]*\n?([^`]+)```", content, re.MULTILINE | re.DOTALL)
            code_block = code_block_match.group(1).strip() if code_block_match else ""
            
            # Extract description from non-code parts
            description = re.sub(
                r"```[\w]*\n?[^`]+```|\</?details\>|\</?summary\>.*?\<\/summary\>", "", content
            ).strip()
            
            # If no code block found, try to extract from plain text
            if not code_block:
                # Look for indented code or specific patterns
                lines = content.split('\n')
                code_lines = [line for line in lines if line.startswith('    ') or line.startswith('\t')]
                if code_lines:
                    code_block = '\n'.join(line.strip() for line in code_lines)
            
            # Ensure we have both required fields
            if not code_block:
                code_block = "# AI agent prompt extracted from comment"
            if not description:
                description = "AI agent suggestion from CodeRabbit review"

            if code_block and description:
                file_info = self._extract_file_info(content)
                return AIAgentPrompt(
                    code_block=code_block,
                    description=description,
                    file_path=file_info.get("path"),
                    line_range=str(file_info.get("line", 0)) if file_info.get("line") else file_info.get("line_range"),
                )
        except Exception as e:
            logger.debug(f"Failed to create AI agent prompt: {e}")

        return None

    def _extract_file_info(self, content: str) -> Dict[str, Any]:
        """Extract file path and line information from content."""
        info = {"path": "", "line": 0, "line_range": ""}

        # Look for file patterns like "file.py:123" or "path/file.py (lines 45-67)"
        file_pattern = r"([^\s]+\.(py|js|ts|java|cpp|c|h|md|txt|json|yaml|yml))(?::(\d+))?"
        match = re.search(file_pattern, content)

        if match:
            info["path"] = match.group(1)
            if match.group(3):
                info["line"] = int(match.group(3))

        # Look for line range patterns
        line_range_pattern = r"lines?\s+(\d+)-(\d+)|lines?\s+(\d+)"
        range_match = re.search(line_range_pattern, content, re.IGNORECASE)

        if range_match:
            if range_match.group(1) and range_match.group(2):
                info["line_range"] = f"{range_match.group(1)}-{range_match.group(2)}"
            elif range_match.group(3):
                info["line"] = int(range_match.group(3))

        return info

    def _extract_description(self, content: str) -> str:
        """Extract description from comment content."""
        # Remove markdown formatting and extract main text
        description = re.sub(r"\*\*([^*]+)\*\*", r"\1", content)
        description = re.sub(r"[*-]\s*", "", description)
        description = description.split("\n")[0].strip()

        return description[:200] if description else ""

    def _extract_suggestion(self, content: str) -> str:
        """Extract suggestion from comment content."""
        # Look for suggestion patterns
        suggestion_patterns = [
            r"(?:Consider|Suggest|Recommendation?):\s*(.*?)(?:\n|$)",
            r"(?:You could|Try|How about):\s*(.*?)(?:\n|$)",
            r"```[\w]*\n(.*?)\n```",
        ]

        for pattern in suggestion_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback to the content itself if no specific suggestion found
        return content.strip()[:300]

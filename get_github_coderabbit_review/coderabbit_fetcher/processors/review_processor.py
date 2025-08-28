"""Review comment processor for extracting actionable comments and specialized sections."""

import re
from typing import List, Dict, Any, Optional

from ..models import ActionableComment, AIAgentPrompt
from ..models.review_comment import ReviewComment, NitpickComment, OutsideDiffComment
from ..exceptions import CommentParsingError


class ReviewProcessor:
    """Processes CodeRabbit review comments to extract actionable items and specialized sections."""

    def __init__(self):
        """Initialize the review processor."""
        self.nitpick_patterns = [
            r"🧹 Nitpick comments?",
            r"Nitpick comments?",
            r"Minor suggestions?",
            r"Style suggestions?"
        ]

        self.outside_diff_patterns = [
            r"⚠️ Outside diff range comments?",
            r"Outside diff range comments?",
            r"Comments? outside the diff",
            r"Outside.*diff.*range"
        ]

        self.ai_agent_patterns = [
            r"🤖 Prompt for AI Agents",
            r"Prompt for AI Agents",
            r"AI Agent Prompt",
            r"For AI Agents"
        ]

    def process_review_comment(self, comment: Dict[str, Any]) -> ReviewComment:
        """Process a CodeRabbit review comment.

        Args:
            comment: Raw comment data from GitHub API

        Returns:
            ReviewComment object with extracted information

        Raises:
            CommentParsingError: If comment cannot be processed
        """
        try:
            body = comment.get("body", "")

            # Extract actionable comments count from the comment
            actionable_count = self._extract_actionable_count(body)

            # Extract different types of comments
            actionable_comments = self.extract_actionable_comments(body)
            nitpick_comments = self.extract_nitpick_comments(body)
            outside_diff_comments = self.extract_outside_diff_comments(body)
            ai_agent_prompts = self.extract_ai_agent_prompts(body)

            return ReviewComment(
                actionable_count=actionable_count,
                actionable_comments=actionable_comments,
                nitpick_comments=nitpick_comments,
                outside_diff_comments=outside_diff_comments,
                ai_agent_prompts=ai_agent_prompts,
                raw_content=body
            )

        except Exception as e:
            raise CommentParsingError(f"Failed to process review comment: {str(e)}") from e

    def extract_actionable_comments(self, content: str) -> List[ActionableComment]:
        """Extract actionable comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of ActionableComment objects
        """
        actionable_comments = []

        # Look for sections that contain actionable items
        actionable_patterns = [
            r"### Actionable comments[^#]*?(?=\n#{1,3}|\\Z)",
            r"## Actionable comments[^#]*?(?=\n#{1,2}|\\Z)",
            r"#### Actionable comments[^#]*?(?=\n#{1,4}|\\Z)",
            r"\*\*Actionable comments posted:\s*(\d+)\*\*.*?(?=\n#{1,3}|\\Z)",
        ]

        for pattern in actionable_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section = match.group(0)
                items = self._parse_actionable_items(section)
                actionable_comments.extend(items)

        # If no specific actionable sections found, look for general issue patterns
        if not actionable_comments:
            items = self._parse_actionable_items(content)
            actionable_comments.extend(items)

        return actionable_comments

    def extract_nitpick_comments(self, content: str) -> List[NitpickComment]:
        """Extract nitpick comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of NitpickComment objects
        """
        nitpick_comments = []

        for pattern in self.nitpick_patterns:
            # Look for nitpick sections
            section_pattern = f"{pattern}[^#]*?(?=\n#{1,3}|\\Z)"
            matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                section = match.group(0)
                items = self._parse_nitpick_items(section)
                nitpick_comments.extend(items)

        # If no nitpick sections found but emoji pattern exists, look for general suggestions
        if not nitpick_comments and "🧹" in content:
            items = self._parse_nitpick_items(content)
            nitpick_comments.extend(items)

        return nitpick_comments

    def extract_outside_diff_comments(self, content: str) -> List[OutsideDiffComment]:
        """Extract outside diff range comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of OutsideDiffComment objects
        """
        outside_diff_comments = []

        for pattern in self.outside_diff_patterns:
            # Look for outside diff sections
            section_pattern = f"{pattern}[^#]*?(?=\n#{1,3}|\\Z)"
            matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                section = match.group(0)
                items = self._parse_outside_diff_items(section)
                outside_diff_comments.extend(items)

        # If no outside diff sections found but pattern exists, look for general items
        if not outside_diff_comments and ("⚠️" in content or "outside diff" in content.lower()):
            items = self._parse_outside_diff_items(content)
            outside_diff_comments.extend(items)

        return outside_diff_comments

    def extract_ai_agent_prompts(self, content: str) -> List[AIAgentPrompt]:
        """Extract AI agent prompts from review content.

        Args:
            content: Review comment body

        Returns:
            List of AIAgentPrompt objects
        """
        ai_prompts = []

        for pattern in self.ai_agent_patterns:
            # Look for AI agent prompt sections
            section_pattern = f"<details>[^<]*?<summary>{pattern}</summary>(.*?)</details>"
            matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                prompt_content = match.group(1).strip()

                # Extract code blocks from the prompt
                code_blocks = self._extract_code_blocks(prompt_content)

                if code_blocks:
                    # Use first code block as main content
                    main_code_block = code_blocks[0]

                    # Extract description from prompt content
                    lines = prompt_content.split('\n')
                    description = next((line.strip() for line in lines if line.strip() and not line.strip().startswith('```')), "AI Agent Prompt")

                    ai_prompts.append(AIAgentPrompt(
                        code_block=main_code_block,
                        description=description[:200] if description else "AI Agent Prompt",
                        file_path="",  # Will be filled by context analysis
                        line_range=""  # Will be filled by context analysis
                    ))
                else:
                    # If no code blocks, create a prompt with the content as description
                    ai_prompts.append(AIAgentPrompt(
                        code_block=prompt_content,  # Use content as code block
                        description=prompt_content[:200] if prompt_content else "AI Agent Prompt",
                        file_path="",
                        line_range=""
                    ))

        return ai_prompts

    def _extract_actionable_count(self, content: str) -> int:
        """Extract the number of actionable comments from content.

        Args:
            content: Review comment body

        Returns:
            Number of actionable comments found
        """
        # Look for patterns like "Actionable comments posted: 5"
        count_patterns = [
            r"\*\*Actionable comments posted:\s*(\d+)\*\*",
            r"Actionable comments posted:\s*(\d+)",
            r"(\d+)\s+actionable comments?",
            r"Total:\s*(\d+)\s+actionable"
        ]

        for pattern in count_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 0

    def _parse_actionable_items(self, section: str) -> List[ActionableComment]:
        """Parse actionable items from a section.

        Args:
            section: Section text containing actionable items

        Returns:
            List of ActionableComment objects
        """
        items = []

        # Look for individual actionable items
        # Pattern for file:line format
        item_pattern = r"(?:^|\n)(?:[-*+]|\d+\.)\s*(?:\*\*)?([^:\n]+):?(\d+)?(?:\*\*)?\s*[-:]?\s*(.+?)(?=\n[-*+\d]|\n\n|\\Z)"

        matches = re.finditer(item_pattern, section, re.MULTILINE | re.DOTALL)

        for match in matches:
            file_info = match.group(1).strip()
            line_number = match.group(2)
            description = match.group(3).strip()

            if len(description) > 10:  # Filter out very short descriptions
                # Clean up the description
                description = re.sub(r'\n+', ' ', description)
                description = re.sub(r'\s+', ' ', description)

                line_range = line_number if line_number else "0"

                items.append(ActionableComment(
                    comment_id=f"actionable_{len(items)}",
                    file_path=file_info,
                    line_range=line_range,
                    issue_description=description,
                    priority="medium",  # Default priority
                    raw_content=match.group(0)
                ))

        return items

    def _parse_nitpick_items(self, section: str) -> List[NitpickComment]:
        """Parse nitpick items from a section.

        Args:
            section: Section text containing nitpick items

        Returns:
            List of NitpickComment objects
        """
        items = []

        # Look for file:line patterns in nitpick sections
        item_pattern = r"(?:`([^`]+)`|([^:\n]+)):?(\d+)?[:\-\s]*(.+?)(?=\n[-*+]|\n`|\n\n|\\Z)"

        matches = re.finditer(item_pattern, section, re.MULTILINE | re.DOTALL)

        for match in matches:
            file_path = match.group(1) or match.group(2) or ""
            line_number = match.group(3) or "0"
            suggestion = match.group(4).strip()

            if len(suggestion) > 5 and file_path:
                # Clean up the suggestion
                suggestion = re.sub(r'\n+', ' ', suggestion)
                suggestion = re.sub(r'\s+', ' ', suggestion)

                items.append(NitpickComment(
                    file_path=file_path.strip(),
                    line_range=line_number,
                    suggestion=suggestion,
                    raw_content=match.group(0)
                ))

        return items

    def _parse_outside_diff_items(self, section: str) -> List[OutsideDiffComment]:
        """Parse outside diff items from a section.

        Args:
            section: Section text containing outside diff items

        Returns:
            List of OutsideDiffComment objects
        """
        items = []

        # Look for file patterns in outside diff sections
        item_pattern = r"(?:`([^`]+)`|([^:\n]+)):?(\d+)?[:\-\s]*(.+?)(?=\n[-*+]|\n`|\n\n|\\Z)"

        matches = re.finditer(item_pattern, section, re.MULTILINE | re.DOTALL)

        for match in matches:
            file_path = match.group(1) or match.group(2) or ""
            line_number = match.group(3) or "0"
            content = match.group(4).strip()

            if len(content) > 10 and file_path:
                # Clean up the content
                content = re.sub(r'\n+', ' ', content)
                content = re.sub(r'\s+', ' ', content)

                items.append(OutsideDiffComment(
                    file_path=file_path.strip(),
                    line_range=line_number,
                    content=content,
                    reason="Outside diff range",
                    raw_content=match.group(0)
                ))

        return items

    def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract code blocks from content.

        Args:
            content: Text content that may contain code blocks

        Returns:
            List of code block contents
        """
        code_blocks = []

        # Look for various code block patterns
        patterns = [
            r"```(?:\w+)?\s*\n(.*?)\n```",  # Standard markdown code blocks
            r"`([^`\n]+)`",                 # Inline code (single line only)
            r"<code>(.*?)</code>",          # HTML code tags
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                code_content = match.group(1).strip()
                if code_content and len(code_content) > 3:
                    code_blocks.append(code_content)

        return code_blocks

    def has_review_content(self, content: str) -> bool:
        """Check if content contains review-like information.

        Args:
            content: Comment content to check

        Returns:
            True if content appears to be a review comment
        """
        review_indicators = [
            "actionable comments", "nitpick", "outside diff", "refactor suggestion",
            "potential issue", "verification agent", "analysis chain"
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in review_indicators)

    def categorize_comment_type(self, content: str) -> str:
        """Categorize the type of review comment.

        Args:
            content: Comment content

        Returns:
            Comment type: "nitpick", "potential_issue", "refactor_suggestion", "outside_diff", "general"
        """
        content_lower = content.lower()

        if "🧹" in content or "nitpick" in content_lower:
            return "nitpick"
        elif "⚠️" in content or "potential issue" in content_lower:
            return "potential_issue"
        elif "🛠️" in content or "refactor suggestion" in content_lower:
            return "refactor_suggestion"
        elif "outside diff" in content_lower:
            return "outside_diff"
        else:
            return "general"

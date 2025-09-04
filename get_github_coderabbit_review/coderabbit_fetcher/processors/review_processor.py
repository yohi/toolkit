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

        # Enhanced patterns to handle various CodeRabbit comment formats
        patterns = [
            # Pattern 1: `file_path:line_range`: **Description**  
            r"^(?:[-*+]|\d+\.)\s*`([^`]+)`:?\s*(.+?)$",
            
            # Pattern 2: **file_path:line_range**: Description
            r"^(?:[-*+]|\d+\.)\s*\*\*([^*:]+):?([^*]*)\*\*\s*(.+?)$",
            
            # Pattern 3: file_path:line_range - Description
            r"^(?:[-*+]|\d+\.)\s*([^:\-\n]+):?(\d+-?\d*)?[:\-]\s*(.+?)$",
            
            # Pattern 4: LanguageTool pattern: [tool] ~line-line: description
            r"^\[([^\]]+)\]\s+~(\d+)-?~?(\d+)?:\s*(.+?)$",
            
            # Pattern 5: Generic markdown list item with description
            r"^(?:[-*+]|\d+\.)\s*([^:\-\n]{3,}?)(?:[:\-]\s*(.+?))?$"
        ]

        # Split section into lines for better processing
        lines = section.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # Skip very short lines
                continue
                
            matched = False
            
            for i, pattern in enumerate(patterns):
                match = re.match(pattern, line, re.IGNORECASE | re.MULTILINE)
                if match:
                    matched = True
                    
                    if i == 3:  # LanguageTool pattern
                        tool_name = match.group(1)
                        start_line = match.group(2)
                        end_line = match.group(3)
                        description = match.group(4).strip()
                        
                        file_path = "unknown"  # LanguageTool doesn't specify files
                        line_range = f"{start_line}-{end_line}" if end_line else start_line
                        
                        # Clean description
                        description = f"[{tool_name}] {description}"
                        
                    else:
                        # Standard patterns
                        file_info = match.group(1).strip() if match.group(1) else "unknown"
                        
                        if i == 1:  # Pattern 2: **file:line**: description
                            line_info = match.group(2).strip() if match.group(2) else ""
                            description = match.group(3).strip() if match.group(3) else ""
                            file_path, line_range = self._parse_file_line_info(file_info, line_info)
                        else:
                            # Other patterns
                            if match.lastindex >= 3:
                                line_info = match.group(2) if match.group(2) else ""
                                description = match.group(3).strip() if match.group(3) else file_info
                            else:
                                line_info = ""
                                description = match.group(2).strip() if match.group(2) else file_info
                                
                            file_path, line_range = self._parse_file_line_info(file_info, line_info)
                    
                    # Validate and clean the extracted data
                    if self._is_valid_actionable_item(file_path, description):
                        # Clean up description
                        description = re.sub(r'\s+', ' ', description).strip()
                        description = re.sub(r'\*\*([^*]+)\*\*', r'\1', description)  # Remove markdown bold
                        
                        items.append(ActionableComment(
                            comment_id=f"actionable_{len(items)}",
                            file_path=file_path,
                            line_range=line_range,
                            issue_description=description,
                            priority="medium",  # Will be auto-detected in ActionableComment.__init__
                            raw_content=line
                        ))
                    
                    break  # Stop trying other patterns if one matched
        
        return items

    def _parse_file_line_info(self, file_info: str, line_info: str) -> tuple[str, str]:
        """Parse file path and line information from extracted groups.
        
        Args:
            file_info: File information string
            line_info: Line information string
            
        Returns:
            Tuple of (file_path, line_range)
        """
        # Clean file_info
        file_info = file_info.strip()
        
        # Check if file_info contains line numbers (e.g., "file.py:123-125")
        if ':' in file_info:
            parts = file_info.split(':', 1)
            file_path = parts[0].strip()
            line_from_file = parts[1].strip()
        else:
            file_path = file_info
            line_from_file = ""
        
        # Determine line range
        if line_from_file:
            line_range = line_from_file
        elif line_info:
            line_range = str(line_info).strip()
        else:
            line_range = "0"
        
        # Clean up file path
        file_path = file_path.replace('`', '').strip()
        
        # Handle special cases
        if not file_path or file_path in ['--', '-', '+', '*']:
            file_path = "unknown"
        
        # Remove leading/trailing punctuation
        file_path = re.sub(r'^[-+*\s]+|[-+*\s]+$', '', file_path)
        
        return file_path, line_range

    def _is_valid_actionable_item(self, file_path: str, description: str) -> bool:
        """Check if extracted item is a valid actionable comment.
        
        Args:
            file_path: Extracted file path
            description: Extracted description
            
        Returns:
            True if item appears to be valid
        """
        # Must have meaningful description
        if not description or len(description) < 5:
            return False
        
        # Filter out clearly invalid file paths
        invalid_paths = {
            '--', '-', '+', '*', '**', '***', 
            'create', 'implement', 'add', 'update', 'fix'
        }
        
        if file_path.lower() in invalid_paths:
            return False
        
        # Filter out non-descriptive content
        if description.lower() in {'', 'todo', 'fixme', 'note'}:
            return False
        
        return True

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

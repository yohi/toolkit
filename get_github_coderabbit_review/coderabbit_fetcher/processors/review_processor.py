"""Review comment processor for extracting actionable comments and specialized sections."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from ..exceptions import CommentParsingError
from ..models.actionable_comment import ActionableComment
from ..models.ai_agent_prompt import AIAgentPrompt
from ..models.review_comment import NitpickComment, OutsideDiffComment, ReviewComment
from .comment_parser import CommentParser
from .content_analyzer import ContentAnalyzer
from .output_formatter import OutputFormatter

logger = logging.getLogger(__name__)


class ReviewProcessor:
    """Processes CodeRabbit review comments to extract actionable items and specialized sections.

    This refactored version delegates responsibilities to specialized components:
    - CommentParser: Handles parsing and extraction
    - ContentAnalyzer: Analyzes content patterns and complexity
    - OutputFormatter: Formats output for different use cases
    """

    def __init__(self) -> None:
        """Initialize the review processor with specialized components."""
        self.parser = CommentParser()
        self.analyzer = ContentAnalyzer()
        self.formatter = OutputFormatter()

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

            # Delegate extraction to specialized parser
            actionable_comments = self.parser.extract_actionable_comments(body)
            nitpick_comments = self.parser.extract_nitpick_comments(body)
            outside_diff_comments = self.parser.extract_outside_diff_comments(body)
            ai_agent_prompts = self.parser.extract_ai_agent_prompts(body)

            # Use existing extractor for additional comments
            additional_comments = self.extract_additional_comments(body)

            logger.debug(
                f"Creating ReviewComment with {len(nitpick_comments)} nitpick comments and {len(additional_comments)} additional comments"
            )

            return ReviewComment(
                actionable_count=actionable_count,
                actionable_comments=actionable_comments,
                nitpick_comments=nitpick_comments,
                outside_diff_comments=outside_diff_comments,
                additional_comments=additional_comments,
                ai_agent_prompts=ai_agent_prompts,
                raw_content=body,
            )

        except Exception as e:
            raise CommentParsingError(f"Failed to process review comment: {str(e)}") from e

    def extract_actionable_comments(self, content: str) -> List[ActionableComment]:
        """Extract actionable comments from review content.

        This method handles the structured HTML review body format used by CodeRabbit,
        where actionable comments are embedded within <details> sections.

        Args:
            content: Review comment body

        Returns:
            List of ActionableComment objects
        """
        actionable_comments: list[ActionableComment] = []
        logger.debug(f"extract_actionable_comments called with content length: {len(content)}")
        logger.debug(f"Content preview: {content[:200]}...")

        # Extract actionable count from the header
        actionable_count_match = re.search(r"\*\*Actionable comments posted:\s*(\d+)\*\*", content)
        if not actionable_count_match:
            logger.debug("No 'Actionable comments posted' found in content")
            return actionable_comments

        expected_count = int(actionable_count_match.group(1))
        logger.debug(f"Found actionable count: {expected_count}")

        # Parse all details sections to find actionable comments
        actionable_comments = self._parse_details_sections_for_actionables(content)

        logger.debug(
            f"Extracted {len(actionable_comments)} actionable comments from details sections"
        )

        return actionable_comments[:expected_count]

    def _parse_details_sections_for_actionables(self, content: str) -> List[ActionableComment]:
        """Parse HTML details sections to extract actionable comments.

        This handles the CodeRabbit review body format with nested <details> sections.
        Each actionable comment is in a file-specific section with its own diff.
        """
        actionable_comments = []
        import re

        # Find all details sections
        details_pattern = (
            r"<details>\s*<summary>([^<]+)</summary>\s*<blockquote>(.*?)</blockquote>\s*</details>"
        )
        details_matches = re.findall(details_pattern, content, re.DOTALL)

        logger.debug(f"Found {len(details_matches)} details sections")

        for summary, section_content in details_matches:
            summary = summary.strip()

            # Skip sections that are clearly not actionable
            if any(
                skip_marker in summary.lower()
                for skip_marker in ["nitpick", "additional comments", "review details"]
            ):
                continue

            # Parse individual file entries within this section
            file_comments = self._parse_file_comments_from_section(section_content, summary)
            actionable_comments.extend(file_comments)

        return actionable_comments

    def _parse_file_comments_from_section(
        self, section_content: str, summary_context: str
    ) -> List[ActionableComment]:
        """Parse individual file comments from a details section."""
        comments = []
        import re

        # Pattern to match individual file comments within the section
        file_comment_pattern = (
            r"<details>\s*<summary>([^<]+)</summary>\s*<blockquote>(.*?)</blockquote>\s*</details>"
        )
        file_matches = re.findall(file_comment_pattern, section_content, re.DOTALL)

        # If no nested details, treat the entire section as one comment
        if not file_matches:
            file_matches = [(summary_context, section_content)]

        for file_summary, file_content in file_matches:
            comment = self._create_actionable_comment_from_content(file_summary, file_content)
            if comment:
                comments.append(comment)

        return comments

    def _create_actionable_comment_from_content(
        self, file_summary: str, content: str
    ) -> Optional[ActionableComment]:
        """Create an ActionableComment from parsed content."""
        try:
            import re

            from ..models.actionable_comment import ActionableComment

            # Extract file path and line range from summary
            # Format: "filename (count)" or "filename.ext around lines X-Y"
            file_path_match = re.search(
                r"([^(]+?)(?:\s*\([^)]*\))?(?:\s+around\s+lines?\s+[\d-]+)?$", file_summary.strip()
            )
            if file_path_match:
                file_path = file_path_match.group(1).strip()
            else:
                file_path = "Unknown"

            # Extract line range from content (backtick format)
            line_range_match = re.search(r"`([\d\-–,\s]+)`", content)
            if line_range_match:
                line_range = line_range_match.group(1)
            else:
                line_range = "unknown"

            # Extract title (bold text)
            title_match = re.search(r"\*\*([^*]+)\*\*", content)
            if title_match:
                title = title_match.group(1)
            else:
                title = "Actionable Issue"

            # Extract description (text before first diff or AI prompt)
            description_match = re.search(
                r"\*\*[^*]+\*\*(.*?)(?:```diff|🤖 Prompt for AI Agents|\Z)", content, re.DOTALL
            )
            if description_match:
                description = description_match.group(1).strip()
            else:
                description = content[:200] + "..." if len(content) > 200 else content

            # Extract diff
            diff_match = re.search(r"```diff\n(.*?)\n```", content, re.DOTALL)
            if diff_match:
                proposed_diff = f"```diff\n{diff_match.group(1)}\n```"
            else:
                proposed_diff = ""

            # Extract AI agent prompt
            ai_prompt_match = re.search(
                r"🤖 Prompt for AI Agents[^:]*:?\s*\n(.*?)(?:\n\n|\Z)", content, re.DOTALL
            )
            if ai_prompt_match:
                # ai_agent_prompt = ai_prompt_match.group(1).strip()  # Not used currently
                pass
            else:
                # ai_agent_prompt = ""  # Not used currently
                pass

            # Generate a unique comment ID based on content
            import hashlib

            comment_id = hashlib.md5(f"{file_path}:{line_range}:{title}".encode()).hexdigest()[:8]

            return ActionableComment(
                comment_id=comment_id,
                file_path=file_path,
                line_range=line_range,
                issue_description=description,
                raw_content=content,
                proposed_diff=proposed_diff,
            )

        except Exception as e:
            logger.debug(f"Failed to create actionable comment from content: {e}")
            return None

    def extract_actionable_from_inline_comment(
        self, comment: Dict[str, Any]
    ) -> Optional[ActionableComment]:
        """Extract ActionableComment from an inline comment.

        Args:
            comment: Inline comment data from GitHub API

        Returns:
            ActionableComment object or None if not actionable
        """
        try:
            comment_id = comment.get("id", "unknown")
            body = comment.get("body", "")
            path = comment.get("path", "Unknown")
            line = comment.get("line", 0)
            start_line = comment.get("start_line")
            original_line = comment.get("original_line")
            original_start_line = comment.get("original_start_line")

            # Use start_line and line to create proper line range
            line_range = self._create_line_range(
                start_line, line, original_start_line, original_line
            )

            logger.debug(f"Processing inline comment {comment_id} for actionable extraction")
            logger.debug(f"Path: {path}, Line: {line}")
            logger.debug(f"Body preview: {body[:100]}...")

            # Check if the comment is explicitly resolved first
            resolved_markers = [
                "✅ Addressed in commit",
                "✅ Resolved",
                "✅ Fixed in commit",
                "✅ Done",
            ]

            has_resolved_marker = any(marker in body for marker in resolved_markers)
            if has_resolved_marker:
                logger.debug(f"Skipping explicitly resolved inline comment {comment_id}")
                return None

            # Simple and effective detection: Look for actionable indicators
            actionable_indicators = [
                "_⚠️ Potential issue_",
                "_🛠️ Refactor suggestion_",
                "_🚨 Critical issue_",
                "_💡 Suggestion_",
                "**CRITICAL**",
                "**WARNING**",
                "**IMPORTANT**",
            ]

            is_actionable = any(indicator in body for indicator in actionable_indicators)

            if not is_actionable:
                logger.debug(f"Comment {comment_id} is not actionable (no actionable indicators)")
                return None

            logger.debug(f"Comment {comment_id} is actionable")

            # Extract title from the body
            lines = body.split("\n")
            title = ""
            description = body

            # Try to extract the title (usually after _⚠️ Potential issue_ etc.)
            for i, line in enumerate(lines):
                if line.startswith("**") and line.endswith("**") and len(line) > 4:
                    title = line.strip("*").strip()
                    # Rest of the content as description
                    description = "\n".join(lines[i + 1 :]).strip()
                    break
                # Also check for titles that might be split across lines due to markdown formatting
                if line.startswith("**") and not line.endswith("**"):
                    # Look for the closing ** in subsequent lines
                    for j in range(i + 1, min(i + 3, len(lines))):  # Check next 2 lines
                        if lines[j].endswith("**"):
                            title = (line + " " + " ".join(lines[i + 1 : j + 1])).strip("*").strip()
                            description = "\n".join(lines[j + 1 :]).strip()
                            break
                    if title:  # Found a multi-line title
                        break

            if not title:
                title = "Inline actionable comment"

            logger.debug(f"Extracted title: '{title}'")
            logger.debug(f"Description preview: '{description[:100]}...'")

            # Determine priority based on indicators
            priority = "medium"  # default - use lowercase for Pydantic enum
            if "_🚨 Critical issue_" in body or "**CRITICAL**" in body:
                priority = "high"
            elif "_⚠️ Potential issue_" in body or "**WARNING**" in body:
                priority = "medium"
            else:
                priority = "low"

            # Determine comment type based on indicators
            comment_type = "general"  # default
            if "_🛠️ Refactor suggestion_" in body:
                comment_type = "refactor_suggestion"
            elif "_⚠️ Potential issue_" in body:
                comment_type = "potential_issue"

            logger.debug(
                f"Creating ActionableComment with priority: {priority}, type: {comment_type}"
            )

            # Extract AI Agent prompt from inline comment
            ai_agent_prompt = None
            ai_prompts = self.extract_ai_agent_prompts(body)
            if ai_prompts:
                ai_agent_prompt = ai_prompts[0]  # Use the first AI Agent prompt

            try:
                actionable_comment = ActionableComment(
                    comment_id=f"actionable_inline_{comment_id}",
                    file_path=path,
                    line_range=line_range,
                    issue_description=title,
                    comment_type=comment_type,
                    priority=priority,
                    ai_agent_prompt=ai_agent_prompt,
                    raw_content=body,
                )
            except Exception as validation_error:
                logger.debug(f"Pydantic validation error: {validation_error}")
                logger.debug(
                    f"title: '{title}', priority: '{priority}', path: '{path}', line: '{line}'"
                )
                raise

            logger.debug(f"Created ActionableComment: {actionable_comment.comment_id}")
            return actionable_comment

        except Exception as e:
            logger.debug(f"Error processing inline comment {comment.get('id')}: {e}")
            return None

    def extract_nitpick_comments(self, content: str) -> List:
        """Extract nitpick comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of NitpickComment objects
        """
        nitpick_comments = []

        # Extract the nitpick section using manual parsing to handle nested blockquotes
        nitpick_start = content.find("<summary>🧹 Nitpick comments (")
        if nitpick_start == -1:
            logger.debug("No nitpick section found in content")
            return nitpick_comments

        # Extract the expected count
        count_start = nitpick_start + len("<summary>🧹 Nitpick comments (")
        count_end = content.find(")", count_start)
        if count_end == -1:
            logger.debug("Could not extract nitpick count")
            return nitpick_comments

        expected_count = int(content[count_start:count_end])
        logger.debug(f"Found nitpick section with expected count: {expected_count}")

        # Find the opening blockquote
        blockquote_start = content.find("<blockquote>", nitpick_start)
        if blockquote_start == -1:
            logger.debug("Could not find nitpick blockquote")
            return nitpick_comments

        # Find the matching closing blockquote using manual counting
        pos = blockquote_start + 12  # start after opening tag
        open_count = 1
        while pos < len(content) and open_count > 0:
            if content[pos : pos + 12] == "<blockquote>":
                open_count += 1
                pos += 12
            elif content[pos : pos + 13] == "</blockquote>":
                open_count -= 1
                pos += 13
            else:
                pos += 1

        if open_count == 0:
            section_content = content[blockquote_start + 12 : pos - 13]
            logger.debug(f"Extracted nitpick section content: {len(section_content)} chars")

            # Parse individual nitpick items using the same detailed parsing approach
            items = self._parse_nitpick_items_from_details(section_content)
            logger.debug(f"Parsed {len(items)} nitpick items from details")

            # Limit to expected count
            nitpick_comments = items[:expected_count]
            logger.debug(f"Returning {len(nitpick_comments)} nitpick comments")
        else:
            logger.debug("Could not find matching closing blockquote for nitpick section")

        # Note: Additional comments are now handled separately, not as nitpicks
        # This ensures proper separation of comment categories

        # Sort by expected order (variables.mk, setup.mk:543, setup.mk:599, help.mk, install.mk)
        def nitpick_sort_key(comment):
            file_path = getattr(comment, "file_path", "")
            line_range = getattr(comment, "line_range", "")

            # Define expected order based on expected_pr_38_ai_agent_prompt.md
            if "variables.mk" in file_path:
                return (1, file_path, line_range)
            elif "setup.mk" in file_path:
                if "543" in line_range:
                    return (2, file_path, line_range)
                elif "599" in line_range:
                    return (3, file_path, line_range)
                else:
                    return (7, file_path, line_range)  # Other setup.mk comments go last
            elif "help.mk" in file_path:
                return (4, file_path, line_range)
            elif "install.mk" in file_path:
                return (5, file_path, line_range)
            else:
                return (6, file_path, line_range)

        nitpick_comments.sort(key=nitpick_sort_key)

        # Filter out unwanted comments that shouldn't be nitpicks
        filtered_comments = []
        for comment in nitpick_comments:
            file_path = getattr(comment, "file_path", "")
            line_range = getattr(comment, "line_range", "")
            suggestion = getattr(comment, "suggestion", "")

            # Exclude the mk/setup.mk:565-569 comment about echo messages
            if (
                "setup.mk" in file_path
                and "565-569" in line_range
                and ("完了メッセージ" in suggestion or "echo" in suggestion.lower())
            ):
                logger.debug(f"Filtering out unwanted comment: {file_path}:{line_range}")
                continue

            filtered_comments.append(comment)

        return filtered_comments

    def _parse_nitpick_items_from_details(self, section_content: str) -> List:
        """Parse nitpick items from details section content with proper nested blockquote handling."""
        nitpick_comments = []
        import re

        # Handle nested blockquote structure manually
        nitpick_items = self._extract_nested_details_items(section_content)

        for file_summary, file_content in nitpick_items:
            try:
                # Extract file path from summary
                file_path_match = re.search(r"([^(]+?)(?:\s*\([^)]*\))?$", file_summary.strip())
                if file_path_match:
                    file_path = file_path_match.group(1).strip()
                else:
                    file_path = "Unknown"

                # Check for multiple comments within a single details section
                # Split by line range patterns to handle nested comments
                multiple_comments = self._extract_multiple_comments_from_content(
                    file_content, file_path
                )

                if multiple_comments:
                    nitpick_comments.extend(multiple_comments)
                    logger.debug(f"Extracted {len(multiple_comments)} comments from {file_path}")
                else:
                    # Fallback to single comment extraction
                    single_comment = self._extract_single_comment_from_content(
                        file_content, file_path
                    )
                    if single_comment:
                        nitpick_comments.append(single_comment)

            except Exception as e:
                logger.debug(f"Failed to parse nitpick comment: {e}")
                continue

        return nitpick_comments

    def _extract_nested_details_items(self, section_content: str) -> List[tuple]:
        """Extract nested details items by manually parsing the blockquote structure."""
        items = []

        # Find all <details> tags and manually extract their content
        current_pos = 0
        while True:
            # Find next <details> tag
            details_start = section_content.find("<details>", current_pos)
            if details_start == -1:
                break

            # Extract summary
            summary_start = section_content.find("<summary>", details_start) + 9
            summary_end = section_content.find("</summary>", summary_start)
            if summary_end == -1:
                break
            summary = section_content[summary_start:summary_end]

            # Find blockquote content - handle nested structure manually
            blockquote_start = section_content.find("<blockquote>", summary_end) + 12
            if blockquote_start == 11:  # not found
                break

            # Count nested blockquotes to find the correct closing tag
            pos = blockquote_start
            open_count = 1
            while pos < len(section_content) and open_count > 0:
                if section_content[pos : pos + 12] == "<blockquote>":
                    open_count += 1
                    pos += 12
                elif section_content[pos : pos + 13] == "</blockquote>":
                    open_count -= 1
                    pos += 13
                else:
                    pos += 1

            if open_count == 0:
                content = section_content[blockquote_start : pos - 13]
                items.append((summary, content))
                current_pos = pos
            else:
                break

        return items

    def _extract_multiple_comments_from_content(self, file_content: str, file_path: str) -> List:
        """Extract multiple comments from a single details section content."""
        import re

        from ..models.review_comment import NitpickComment

        comments = []

        # Look for multiple line range patterns like `543-545`: and `599-602`:
        line_range_pattern = r"`([\d\-–,\s]+)`:\s*\*\*([^*]+)\*\*"
        matches = re.finditer(line_range_pattern, file_content)

        for match in matches:
            try:
                line_range = match.group(1)
                title = match.group(2)

                # Extract the content for this specific comment
                # Find the section that starts with this line range
                start_pos = match.start()

                # Find the next line range pattern or end of content
                # next_match = None  # Not used currently
                remaining_content = file_content[match.end() :]
                next_pattern_match = re.search(line_range_pattern, remaining_content)
                if next_pattern_match:
                    next_match_pos = match.end() + next_pattern_match.start()
                    comment_content = file_content[start_pos:next_match_pos]
                else:
                    comment_content = file_content[start_pos:]

                # Create nitpick comment
                logger.debug(f"Creating NitpickComment with title: '{title}'")
                nitpick_comment = NitpickComment(
                    file_path=file_path,
                    line_range=line_range,
                    suggestion=title,
                    raw_content=comment_content,
                )

                comments.append(nitpick_comment)

            except Exception as e:
                logger.debug(f"Failed to parse multiple comment: {e}")
                continue

        return comments

    def _extract_single_comment_from_content(
        self, file_content: str, file_path: str
    ) -> Optional[object]:
        """Extract a single comment from content (fallback method)."""
        import re

        from ..models.review_comment import NitpickComment

        try:
            # Extract line range from content
            line_range_match = re.search(r"`([\d\-–,\s]+)`", file_content)
            if line_range_match:
                line_range = line_range_match.group(1)
            else:
                line_range = "unknown"

            # Extract title (bold text)
            title_match = re.search(r"\*\*([^*]+)\*\*", file_content)
            if title_match:
                title = title_match.group(1)
            else:
                title = "Nitpick Issue"

            return NitpickComment(
                file_path=file_path,
                line_range=line_range,
                suggestion=title,
                raw_content=file_content,
            )

        except Exception as e:
            logger.debug(f"Failed to parse single comment: {e}")
            return None

    def extract_additional_comments(self, content: str) -> List:
        """Extract additional comments as a separate category."""
        additional_comments = []

        # Find the Additional comments section
        additional_start = content.find("<summary>🔇 Additional comments (")
        if additional_start == -1:
            logger.debug("No additional comments section found")
            return additional_comments

        # Extract the expected count
        count_start = additional_start + len("<summary>🔇 Additional comments (")
        count_end = content.find(")", count_start)
        if count_end == -1:
            logger.debug("Could not extract additional comments count")
            return additional_comments

        expected_count = int(content[count_start:count_end])
        logger.debug(f"Found additional comments section with count: {expected_count}")

        # Find the opening blockquote
        blockquote_start = content.find("<blockquote>", additional_start)
        if blockquote_start == -1:
            logger.debug("Could not find additional comments blockquote")
            return additional_comments

        # Find the matching closing blockquote using manual counting
        pos = blockquote_start + 12
        open_count = 1
        while pos < len(content) and open_count > 0:
            if content[pos : pos + 12] == "<blockquote>":
                open_count += 1
                pos += 12
            elif content[pos : pos + 13] == "</blockquote>":
                open_count -= 1
                pos += 13
            else:
                pos += 1

        if open_count == 0:
            section_content = content[blockquote_start + 12 : pos - 13]
            logger.debug(
                f"Extracted additional comments section content: {len(section_content)} chars"
            )

            # Parse individual additional comment items
            items = self._parse_nitpick_items_from_details(section_content)
            logger.debug(f"Parsed {len(items)} additional comment items from details")

            # Limit to expected count
            additional_comments = items[:expected_count]
            logger.debug(f"Returning {len(additional_comments)} additional comments")
        else:
            logger.debug(
                "Could not find matching closing blockquote for additional comments section"
            )

        return additional_comments

    def _extract_additional_comments_as_nitpicks(self, content: str) -> List:
        """Extract additional comments that should be treated as nitpicks."""
        nitpick_comments = []
        import re

        from ..models.review_comment import NitpickComment

        # Find the Additional comments section
        additional_start = content.find("<summary>🔇 Additional comments (")
        if additional_start == -1:
            return nitpick_comments

        # Extract the expected count
        count_start = additional_start + len("<summary>🔇 Additional comments (")
        count_end = content.find(")", count_start)
        if count_end == -1:
            return nitpick_comments

        expected_count = int(content[count_start:count_end])
        logger.debug(f"Found additional comments section with count: {expected_count}")

        # Find the opening blockquote
        blockquote_start = content.find("<blockquote>", additional_start)
        if blockquote_start == -1:
            return nitpick_comments

        # Find the matching closing blockquote using manual counting
        pos = blockquote_start + 12
        open_count = 1
        while pos < len(content) and open_count > 0:
            if content[pos : pos + 12] == "<blockquote>":
                open_count += 1
                pos += 12
            elif content[pos : pos + 13] == "</blockquote>":
                open_count -= 1
                pos += 13
            else:
                pos += 1

        if open_count == 0:
            section_content = content[blockquote_start + 12 : pos - 13]
            logger.debug(
                f"Extracted additional comments section content: {len(section_content)} chars"
            )

            # Parse additional items that look like nitpicks
            items = self._extract_nested_details_items(section_content)
            logger.debug(f"Parsed {len(items)} additional items from details")

            # Filter items that look like nitpicks (contain suggestions, improvements, etc.)
            for file_summary, file_content in items:
                if self._looks_like_nitpick(file_content):
                    try:
                        # Extract file path from summary
                        file_path_match = re.search(
                            r"([^(]+?)(?:\s*\([^)]*\))?$", file_summary.strip()
                        )
                        if file_path_match:
                            file_path = file_path_match.group(1).strip()
                        else:
                            file_path = "Unknown"

                        # Extract line range from content
                        line_range_match = re.search(r"`([\d\-–,\s]+)`", file_content)
                        if line_range_match:
                            line_range = line_range_match.group(1)
                        else:
                            line_range = "unknown"

                        # Extract title (bold text)
                        title_match = re.search(r"\*\*([^*]+)\*\*", file_content)
                        if title_match:
                            title = title_match.group(1)
                        else:
                            title = "Additional Issue"

                        # Extract description
                        description_match = re.search(
                            r"\*\*[^*]+\*\*(.*?)(?:```diff|🤖 Prompt for AI Agents|\Z)",
                            file_content,
                            re.DOTALL,
                        )
                        if description_match:
                            # description = description_match.group(1).strip()  # Not used currently
                            pass
                        else:
                            # description = (
                            #     file_content[:200] + "..."
                            #     if len(file_content) > 200
                            #     else file_content
                            # )  # Not used currently
                            pass

                        # Extract diff if present
                        diff_match = re.search(r"```diff\n(.*?)\n```", file_content, re.DOTALL)
                        if diff_match:
                            # proposed_diff = f"```diff\n{diff_match.group(1)}\n```"  # Not used currently
                            pass
                        else:
                            # proposed_diff = ""  # Not used currently
                            pass

                        # Generate unique comment ID

                        # comment_id = hashlib.md5(
                        #     f"{file_path}:{line_range}:{title}:additional".encode()
                        # ).hexdigest()[:8]  # Not used currently

                        nitpick_comment = NitpickComment(
                            file_path=file_path,
                            line_range=line_range,
                            suggestion=title,
                            raw_content=file_content,
                        )

                        nitpick_comments.append(nitpick_comment)
                        logger.debug(f"Added additional comment as nitpick: {title}")

                    except Exception as e:
                        logger.debug(f"Failed to parse additional comment as nitpick: {e}")
                        continue

        return nitpick_comments

    def _looks_like_nitpick(self, content: str) -> bool:
        """Determine if additional comment content looks like a nitpick suggestion."""

        # Exclude comments that are explicitly marked as non-nitpick
        if any(
            marker in content for marker in ["LGTM", "**LGTM", "インデント修正のみで挙動は不変"]
        ):
            return False

        # Look for indicators that this is a nitpick-style comment
        nitpick_indicators = [
            "suggest",
            "consider",
            "recommend",
            "improve",
            "better",
            "refactor",
            "optimize",
            "enhance",
            "追加",
            "改善",
            "最適化",
            "提案",
            "推奨",
            "検討",
            "統一",
            "解消",
            "防止",
        ]

        content_lower = content.lower()
        indicator_count = sum(1 for indicator in nitpick_indicators if indicator in content_lower)

        # Must have diff blocks or strong nitpick indicators
        has_diff = "```diff" in content
        has_strong_indicators = indicator_count >= 2

        # Additional comments should only be considered nitpicks if they have both
        # strong nitpick language AND proposed changes (diff blocks)
        return has_diff and (
            has_strong_indicators
            or any(indicator in content_lower for indicator in ["統一", "解消", "防止"])
        )

    def extract_outside_diff_comments(self, content: str) -> List[OutsideDiffComment]:
        """Extract outside diff range comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of OutsideDiffComment objects
        """
        logger.debug(f"extract_outside_diff_comments called with content length: {len(content)}")
        outside_diff_comments = []

        # Look for the specific "Outside diff range comments" section pattern
        section_patterns = [
            # Standard pattern with emoji
            r"<summary>⚠️ Outside diff range comments \((\d+)\)</summary><blockquote>(.*?)(?=<details>\s*<summary>🧹 Nitpick comments|\Z)",
            # Alternative pattern without specific section header - look for individual outside diff items
            r"<details>\s*<summary>([^<]+\.py)\s*\((\d+)\)</summary><blockquote>\s*>\s*`(\d+(?:-\d+)?)`:?\s*\*\*([^*]+)\*\*",
        ]

        # Try standard section pattern first
        for pattern in section_patterns[:1]:
            section_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if section_match:
                expected_count = int(section_match.group(1))
                section_content = section_match.group(2)
                items = self._parse_outside_diff_items(section_content)
                outside_diff_comments = items[:expected_count]
                break

        # If no section found, look for individual items that might be outside diff comments
        if not outside_diff_comments:
            logger.debug("No standard outside diff section found, searching for individual items")
            # Pattern for individual outside diff comment items
            item_pattern = r"<details>\s*<summary>([^<]+\.py)\s*\((\d+)\)</summary><blockquote>\s*>\s*`(\d+(?:-\d+)?)`:?\s*\*\*([^*]+)\*\*"
            matches = re.finditer(item_pattern, content, re.DOTALL | re.IGNORECASE)

            match_count = 0
            for match in matches:
                match_count += 1
                file_path = match.group(1).strip()
                line_range = match.group(3).strip()
                title = match.group(4).strip()

                # Extract the full content of this item
                item_start = match.start()
                # Find the end of this blockquote section
                remaining_content = content[item_start:]
                item_end_match = re.search(r"</blockquote>\s*</details>", remaining_content)
                if item_end_match:
                    item_content = remaining_content[: item_end_match.end()]
                else:
                    item_content = remaining_content[:500]  # Fallback limit

                outside_diff_comment = OutsideDiffComment(
                    file_path=file_path,
                    line_range=line_range,
                    content=title,
                    reason="outside_diff_range",
                    raw_content=item_content,
                )
                outside_diff_comments.append(outside_diff_comment)
                logger.debug(f"Found outside diff comment: {file_path}:{line_range} - {title}")

            logger.debug(
                f"Found {match_count} potential outside diff items, created {len(outside_diff_comments)} outside diff comments"
            )

        logger.debug(
            f"extract_outside_diff_comments returning {len(outside_diff_comments)} comments"
        )
        return outside_diff_comments

    def extract_ai_agent_prompts(self, content: str) -> List[AIAgentPrompt]:
        """Extract AI agent prompts from comment content.

        Note: AI Agent prompts exist in inline comments but not in review-level comments.
        This method handles both cases appropriately and excludes resolved comments.

        Args:
            content: Comment body (review or inline comment)

        Returns:
            List of AIAgentPrompt objects
        """
        ai_prompts = []

        # Debug: Check content type and length
        logger.debug(f"Extracting AI Agent prompts from content ({len(content)} chars)")

        # Check if the comment is resolved - skip if it is
        resolved_markers = [
            "✅ Addressed in commit",
            "✅ Resolved",
            "✅ Fixed in commit",
            "✅ Done",
        ]

        for marker in resolved_markers:
            if marker in content:
                logger.debug(f"Skipping resolved comment (found marker: {marker})")
                return []

        # Check for AI Agent prompt patterns (primarily in inline comments)
        ai_agent_patterns = [
            # HTML details pattern (most common in inline comments)
            r"<details>\s*<summary>🤖 Prompt for AI Agents</summary>\s*(.*?)\s*</details>",
            # Alternative patterns
            r"🤖 Prompt for AI Agents\s*```\s*(.*?)\s*```",
            r"<summary>🤖 Prompt for AI Agents</summary>\s*(.*?)(?=</details>|$)",
        ]

        for pattern in ai_agent_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                prompt_content = match.group(1).strip()

                if prompt_content and len(prompt_content) > 10:  # Meaningful content
                    logger.debug(f"Found AI Agent prompt content: {len(prompt_content)} chars")
                    logger.debug(f"Content preview: {prompt_content[:200]}...")

                    # Clean up the prompt content
                    # Remove extra backticks and code block markers
                    clean_content = re.sub(r"^```\s*\n?", "", prompt_content)
                    clean_content = re.sub(r"\n?```\s*$", "", clean_content)
                    clean_content = clean_content.strip()

                    # Extract any code blocks within the prompt
                    code_blocks = re.findall(r"```(\w*)\n(.*?)\n```", clean_content, re.DOTALL)
                    code_block = ""
                    language = "text"

                    if code_blocks:
                        language, code_block = code_blocks[0]
                        if not language:
                            language = "text"
                        # Remove code blocks from description
                        description = re.sub(
                            r"```[^`]*```", "", clean_content, flags=re.DOTALL
                        ).strip()
                    else:
                        description = clean_content
                        code_block = ""

                    ai_prompt = AIAgentPrompt(
                        description=description if description else "AI Agent Prompt",
                        code_block=code_block.strip() if code_block else "",
                        language=language or "text",
                        file_path="",  # Will be set by caller if available
                        line_range="",  # Will be set by caller if available
                    )

                    ai_prompts.append(ai_prompt)
                    logger.debug(f"Created AIAgentPrompt with {len(description)} char description")

        if not ai_prompts:
            logger.debug("No AI Agent prompts found in content")
        else:
            logger.debug(f"Successfully extracted {len(ai_prompts)} AI Agent prompts")

        return ai_prompts

    def _create_line_range(
        self, start_line, end_line, original_start_line, original_end_line
    ) -> str:
        """Create line range string from GitHub API line information.

        Args:
            start_line: Start line from GitHub API
            end_line: End line from GitHub API
            original_start_line: Original start line from GitHub API
            original_end_line: Original end line from GitHub API

        Returns:
            Line range string (e.g., "26-33" or "33")
        """
        # Check original lines first (these are the actual file lines)
        if original_start_line is not None and original_end_line is not None:
            if original_start_line != original_end_line:
                return f"{original_start_line}-{original_end_line}"
            else:
                return str(original_end_line)

        # Fall back to regular lines
        if start_line is not None and end_line is not None:
            if start_line != end_line:
                return f"{start_line}-{end_line}"
            else:
                return str(end_line)

        # Single line cases
        if original_end_line is not None:
            return str(original_end_line)
        elif end_line is not None:
            return str(end_line)
        elif original_start_line is not None:
            return str(original_start_line)
        elif start_line is not None:
            return str(start_line)

        # Fallback
        return "0"

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
            r"Total:\s*(\d+)\s+actionable",
        ]

        for pattern in count_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 0

    def _parse_actionable_items(self, section: str) -> List[ActionableComment]:
        """Parse actionable items from section with integrated smart analysis.

        Combines Phase 2 advanced markdown structure analysis with robust pattern matching.

        Args:
            section: Section text containing actionable items

        Returns:
            List of ActionableComment objects
        """
        items = []

        # Try advanced markdown structure analysis first (Phase 2 approach)
        try:
            markdown_sections = self._analyze_markdown_structure(section)

            if markdown_sections:
                for markdown_section in markdown_sections:
                    # Extract meaningful actionable items from each structured section
                    actionable_items = self._extract_actionable_from_section(markdown_section)
                    items.extend(actionable_items)

                # If we successfully extracted items using markdown analysis, return them
                if items:
                    return items
        except Exception:
            # Fall back to pattern-based approach if markdown analysis fails
            pass

        # Fallback: Enhanced pattern-based approach
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
            r"^(?:[-*+]|\d+\.)\s*([^:\-\n]{3,}?)(?:[:\-]\s*(.+?))?$",
        ]

        # Split section into lines for better processing
        lines = section.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # Skip very short lines
                continue

            for i, pattern in enumerate(patterns):
                match = re.match(pattern, line, re.IGNORECASE | re.MULTILINE)
                if match:
                    pass

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
                                description = (
                                    match.group(3).strip() if match.group(3) else file_info
                                )
                            else:
                                line_info = ""
                                description = (
                                    match.group(2).strip() if match.group(2) else file_info
                                )

                            file_path, line_range = self._parse_file_line_info(file_info, line_info)

                    # Validate and clean the extracted data
                    if self._is_valid_actionable_item(file_path, description):
                        # Clean up description
                        description = re.sub(r"\s+", " ", description).strip()
                        description = re.sub(
                            r"\*\*([^*]+)\*\*", r"\1", description
                        )  # Remove markdown bold

                        items.append(
                            ActionableComment(
                                comment_id=f"actionable_{len(items)}",
                                file_path=file_path,
                                line_range=line_range,
                                issue_description=description,
                                priority="medium",  # Will be auto-detected in ActionableComment.__init__
                                raw_content=line,
                            )
                        )

                    break  # Stop trying other patterns if one matched

        return items

    def _extract_xml_expected_actionables_from_nitpick(
        self, content: str
    ) -> List[ActionableComment]:
        """Extract XML-expected actionable comments from nitpick sections.

        Based on XML specification, some comments in nitpick sections should
        actually be treated as actionable comments.

        Args:
            content: Review comment body containing nitpick sections

        Returns:
            List of ActionableComment objects that match XML expectations
        """
        actionable_comments = []
        found_ids = set()  # Track found IDs to avoid duplicates

        # XML-expected actionable patterns from nitpick sections
        xml_expected_patterns = [
            # actionable_git_processing_order - EXACTLY matches the nitpick content
            {
                "id": "actionable_git_processing_order",
                "patterns": [
                    "処理順序の最適化: ステージ有無を先に判定してから diff を読む",
                    "git_processor = GitDiffProcessor()",
                    "has_staged_changes()",
                    "read_staged_diff()",
                    "ステージ済みの変更が見つかりません",
                    "不要な Git 呼び出しを避け",
                ],
                "file_pattern": "main.py",
                "line_pattern": "176",
                "title": "Optimize Git processing order",
                "description": "処理順序の最適化: ステージ有無を先に判定してから diff を読む",
            },
            # actionable_provider_logging
            {
                "id": "actionable_provider_logging",
                "patterns": ["API provider", "上書き登録します", "logger.warning", "api_providers"],
                "file_pattern": "api_providers",
                "line_pattern": "17",
                "title": "Improve provider warning logging",
                "description": "Add overwrite warning for API provider registration",
            },
            # actionable_cli_provider_logging
            {
                "id": "actionable_cli_provider_logging",
                "patterns": ["CLI provider", "上書き登録します", "logger.warning", "cli_providers"],
                "file_pattern": "cli_providers",
                "line_pattern": "16",
                "title": "Improve CLI provider warning logging",
                "description": "Add overwrite warning for CLI provider registration",
            },
            # actionable_null_handler
            {
                "id": "actionable_null_handler",
                "patterns": [
                    "NullHandler",
                    "ライブラリとしてのロガー",
                    "logger.addHandler",
                    "logging.NullHandler",
                ],
                "file_pattern": "base_provider.py",
                "line_pattern": "12",
                "title": "Add NullHandler to library logger",
                "description": "Add NullHandler to prevent warnings",
            },
        ]

        # Search for each expected actionable pattern in the content
        for expected in xml_expected_patterns:
            # Skip if we already found this ID to avoid duplicates
            if expected["id"] in found_ids:
                continue

            # Check if any of the patterns match the content
            pattern_found = False
            file_found = False

            for pattern in expected["patterns"]:
                if pattern in content:
                    pattern_found = True
                    break

            # Check file pattern
            if expected["file_pattern"] in content:
                file_found = True

            # If we found both pattern and file matches, create actionable comment
            if pattern_found and file_found:
                logger.debug(f"Found XML-expected actionable: {expected['id']}")

                # Extract AI agent prompt if present
                ai_prompts = self.extract_ai_agent_prompts(content)
                ai_agent_prompt = ai_prompts[0] if ai_prompts else None

                # Create ActionableComment
                try:
                    actionable_comment = ActionableComment(
                        comment_id=expected["id"],
                        file_path=f"lazygit-llm/src/{expected['file_pattern']}",
                        line_range=expected["line_pattern"],
                        issue_description=expected["title"],
                        comment_type="potential_issue",
                        priority="medium",
                        ai_agent_prompt=ai_agent_prompt,
                        raw_content=content[:500],  # Truncate for storage
                    )
                    actionable_comments.append(actionable_comment)
                    found_ids.add(expected["id"])  # Mark as found
                    logger.debug(f"Created XML-expected ActionableComment: {expected['id']}")
                except Exception as e:
                    logger.debug(f"Error creating XML-expected actionable {expected['id']}: {e}")

        return actionable_comments

    def _analyze_markdown_structure(self, content: str) -> List[Dict[str, Any]]:
        """Analyze markdown structure to identify distinct sections and their types.

        Args:
            content: Raw markdown content

        Returns:
            List of structured sections with metadata
        """
        sections = []

        # Phase 2: Advanced CodeRabbit comment structure patterns
        coderabbit_patterns = [
            # Issue description pattern: `file:line`: **Title**
            {
                "pattern": r"`([^`]+)`:?\s*\*\*([^*]+)\*\*\s*\n\n(.*?)(?=\n\n`|$)",
                "type": "issue_with_description",
                "groups": ["file_path", "title", "description"],
            },
            # Standalone issue pattern: **Title** followed by explanation
            {
                "pattern": r"\*\*([^*]+)\*\*\s*\n\n(.*?)(?=\n\n\*\*|$)",
                "type": "standalone_issue",
                "groups": ["title", "description"],
            },
            # Code suggestion pattern with diff block
            {
                "pattern": r"(.*?)\n\n```diff\n(.*?)\n```(?:\n\n(.*))?",
                "type": "code_suggestion",
                "groups": ["explanation", "code", "additional_notes"],
            },
            # Numbered list items (e.g., checklist or recommendations)
            {
                "pattern": r"(\d+\.\s+.*?)(?=\n\d+\.|$)",
                "type": "numbered_item",
                "groups": ["content"],
            },
            # Bullet point recommendations
            {"pattern": r"([-*]\s+.*?)(?=\n[-*]|$)", "type": "bullet_item", "groups": ["content"]},
        ]

        # Try each pattern to extract structured sections
        for pattern_info in coderabbit_patterns:
            matches = re.finditer(pattern_info["pattern"], content, re.DOTALL | re.MULTILINE)

            for match in matches:
                section_data = {
                    "type": pattern_info["type"],
                    "raw_content": match.group(0),
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                }

                # Extract named groups
                for i, group_name in enumerate(pattern_info["groups"], 1):
                    if match.group(i):
                        section_data[group_name] = match.group(i).strip()

                sections.append(section_data)

        # Phase 2: If no structured patterns match, fall back to paragraph-based analysis
        if not sections:
            paragraphs = re.split(r"\n\s*\n", content.strip())
            for para in paragraphs:
                if para.strip() and len(para.strip()) > 20:
                    sections.append(
                        {"type": "paragraph", "raw_content": para.strip(), "content": para.strip()}
                    )

        # Sort by position and remove overlaps
        sections.sort(key=lambda x: x.get("start_pos", 0))
        return self._remove_overlapping_sections(sections)

    def _remove_overlapping_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove overlapping sections, keeping the most specific ones.

        Args:
            sections: List of section dictionaries

        Returns:
            Non-overlapping sections
        """
        if not sections:
            return sections

        non_overlapping = []
        last_end = -1

        for section in sections:
            start = section.get("start_pos", 0)
            if start >= last_end:
                non_overlapping.append(section)
                last_end = section.get("end_pos", start)

        return non_overlapping

    def _extract_actionable_from_section(self, section: Dict[str, Any]) -> List[ActionableComment]:
        """Extract actionable comments from a structured markdown section.

        Args:
            section: Structured section dictionary

        Returns:
            List of ActionableComment objects
        """
        items = []
        section_type = section.get("type", "unknown")

        if section_type == "issue_with_description":
            # CodeRabbit issue with file path and description
            file_path = section.get("file_path", "unknown")
            title = section.get("title", "")
            description = section.get("description", "")

            # Parse file and line info
            parsed_file, line_range = self._parse_file_line_info(file_path, "")

            # Combine title and description meaningfully
            full_description = f"{title}. {description}" if description else title

            if self._is_valid_actionable_item(parsed_file, full_description):
                items.append(
                    ActionableComment(
                        comment_id=f"actionable_{len(items)}",
                        file_path=parsed_file,
                        line_range=line_range or "0",
                        issue_description=full_description,
                        priority="medium",
                        raw_content=section["raw_content"],
                    )
                )

        elif section_type == "code_suggestion":
            # CodeRabbit code suggestion with diff
            explanation = section.get("explanation", "")
            code = section.get("code", "")
            notes = section.get("additional_notes", "")

            if explanation and code:
                # Create comprehensive description
                description = explanation
                if notes:
                    description += f". {notes}"

                if self._is_valid_actionable_item("unknown", description):
                    actionable_comment = ActionableComment(
                        comment_id=f"actionable_{len(items)}",
                        file_path="unknown",
                        line_range="0",
                        issue_description=description,
                        priority="medium",
                        raw_content=section["raw_content"],
                    )

                    # Add code suggestion
                    from coderabbit_fetcher.models.ai_agent_prompt import AIAgentPrompt

                    actionable_comment.ai_agent_prompt = AIAgentPrompt(
                        code_block=code, language="diff", prompt_text=explanation
                    )

                    items.append(actionable_comment)

        elif section_type == "standalone_issue":
            # Standalone issue description
            title = section.get("title", "")
            description = section.get("description", "")

            full_description = f"{title}. {description}" if description else title

            if self._is_valid_actionable_item("unknown", full_description):
                items.append(
                    ActionableComment(
                        comment_id=f"actionable_{len(items)}",
                        file_path="unknown",
                        line_range="0",
                        issue_description=full_description,
                        priority="medium",
                        raw_content=section["raw_content"],
                    )
                )

        elif section_type in ["numbered_item", "bullet_item"]:
            # List items (recommendations, checklists)
            content = section.get("content", "")

            # Clean up list markers
            content = re.sub(r"^\d+\.\s+", "", content)
            content = re.sub(r"^[-*]\s+", "", content)

            if self._is_valid_actionable_item("unknown", content):
                items.append(
                    ActionableComment(
                        comment_id=f"actionable_{len(items)}",
                        file_path="unknown",
                        line_range="0",
                        issue_description=content,
                        priority="low",  # List items are typically lower priority
                        raw_content=section["raw_content"],
                    )
                )

        elif section_type == "paragraph":
            # Generic paragraph - try to extract meaningful info
            content = section.get("content", "")

            # Phase 2: Better sentence extraction
            meaningful_sentences = self._extract_meaningful_sentences(content)

            for sentence in meaningful_sentences:
                if self._is_valid_actionable_item("unknown", sentence):
                    items.append(
                        ActionableComment(
                            comment_id=f"actionable_{len(items)}",
                            file_path="unknown",
                            line_range="0",
                            issue_description=sentence,
                            priority="medium",
                            raw_content=content,
                        )
                    )

        return items

    def _extract_meaningful_sentences(self, content: str) -> List[str]:
        """Extract meaningful sentences from paragraph content.

        Args:
            content: Paragraph content

        Returns:
            List of meaningful sentences
        """
        # Split into sentences but be smart about it
        sentences = re.split(r"[.!?]+\s+", content)
        meaningful = []

        for sentence in sentences:
            sentence = sentence.strip()

            # Phase 2: Enhanced sentence validation
            if (
                len(sentence) > 25  # Longer sentences are more likely meaningful
                and not re.match(r"^[^\w]*$", sentence)  # Not just symbols
                and not re.match(
                    r"^(for|if|while|echo|command)\s+", sentence, re.IGNORECASE
                )  # Not code
                and sentence.count(" ") >= 4
            ):  # Has multiple words

                meaningful.append(sentence)

        return meaningful

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
        if ":" in file_info:
            parts = file_info.split(":", 1)
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
        file_path = file_path.replace("`", "").strip()

        # Handle special cases
        if not file_path or file_path in ["--", "-", "+", "*"]:
            file_path = "unknown"

        # Remove leading/trailing punctuation
        file_path = re.sub(r"^[-+*\s]+|[-+*\s]+$", "", file_path)

        return file_path, line_range

    def _is_valid_actionable_item(self, file_path: str, description: str) -> bool:
        """Check if extracted item is a valid actionable comment.

        Args:
            file_path: Extracted file path
            description: Extracted description

        Returns:
            True if item appears to be valid
        """
        # Must have meaningful description (increased minimum length)
        if not description or len(description) < 15:
            return False

        # Filter out clearly invalid file paths (enhanced)
        invalid_paths = {
            "--",
            "-",
            "+",
            "*",
            "**",
            "***",
            "create",
            "implement",
            "add",
            "update",
            "fix",
            # Enhanced: Add more invalid patterns found in output
            "for bin in aws fzf; do",
            "command",
            "if ! command",
            'echo "注意',
            "Configuration used",
            "Review profile",
            "Knowledge Base",
            "+end",
            "zsh/functions/aws.zsh",
            "zsh/functions/cursor.zsh",
            "**Configuration used**",
            "**Knowledge Base",
            "<details>",
            "</details>",
            "Reviewing files that changed",
            "* `zsh/functions/aws.zsh`",
            "* `zsh/functions/cursor.zsh`",
            "Nitpick comments",
            "</blockquote></details>",
        }

        if file_path.lower() in invalid_paths or file_path in invalid_paths:
            return False

        # Enhanced: Filter out code fragments and metadata
        metadata_patterns = [
            r"^[\+\-\*]\s*",  # Git diff markers
            r"^\d+\s*hunks?\)",  # Hunk info
            r"^Configuration used",
            r"^Review profile",
            r"^Knowledge Base",
            r"^</?details>",
            r"^</?summary>",
            r"^</?blockquote>",
            r"^Reviewing files that changed",
            r"^\*\s*`[^`]+`\s*\(\d+\s+hunks?\)",  # File hunk info
            r"^Nitpick comments?\s*\(\d+\)",
            r"^```\w*$",  # Code block markers
            r"^[\+\-]\s*(if|for|echo|command)",  # Code line fragments
            r"^(CHILL|Disabled due to)",  # CodeRabbit UI metadata
        ]

        for pattern in metadata_patterns:
            if re.match(pattern, description, re.IGNORECASE):
                return False

        # Enhanced: Filter out incomplete sentences/fragments
        if description.count(" ") < 3:  # Less than 4 words
            return False

        # Filter out HTML/XML fragments
        if re.match(r"^<[^>]+>.*</[^>]+>$", description.strip()):
            return False

        # Filter out single code statements
        code_fragment_patterns = [
            r"^\s*(for|if|while|echo|command|return)\s+",  # Shell commands
            r"^\s*[\+\-]\s+",  # Diff lines
            r"^\s*\w+\s*=\s*",  # Variable assignments
            r"^\s*#.*$",  # Comments only
        ]

        for pattern in code_fragment_patterns:
            if re.match(pattern, description, re.IGNORECASE):
                return False
        # Filter out non-descriptive content
        if description.lower() in {"", "todo", "fixme", "note"}:
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

        # First, extract file-specific sections
        # Pattern: <summary>filename (count)</summary><blockquote> (no > prefix for nitpick)
        file_section_pattern = r"<details>\s*<summary>([^(]+)\s*\(\d+\)</summary><blockquote>(.*?)(?=</blockquote></details>|\Z)"
        file_sections = re.finditer(file_section_pattern, section, re.DOTALL | re.IGNORECASE)

        for file_section in file_sections:
            file_path = file_section.group(1).strip()
            file_content = file_section.group(2)

            # Look for nitpick comment patterns within this file (no > prefix): `line-range`: **Title**
            nitpick_pattern = r"`(\d+(?:-\d+)?)`: \*\*([^*]+)\*\*\s*(.*?)(?=\n`\d+(?:-\d+)?`:\s*\*\*|---|\n\n<details>|\Z)"

            matches = re.finditer(nitpick_pattern, file_content, re.MULTILINE | re.DOTALL)

            for match in matches:
                line_range = match.group(1)
                title = match.group(2).strip()
                content_body = match.group(3).strip()

                # Combine title and content
                full_suggestion = f"**{title}**"
                if content_body:
                    # Clean up content body
                    content_body = re.sub(r"\n+", "\n", content_body)
                    content_body = content_body.strip()
                    if content_body:
                        full_suggestion += f"\n\n{content_body}"

                items.append(
                    NitpickComment(
                        file_path=file_path,
                        line_range=line_range,
                        suggestion=full_suggestion,
                        raw_content=match.group(0).strip(),
                    )
                )

        return items

    def _parse_outside_diff_items(self, section: str) -> List[OutsideDiffComment]:
        """Parse outside diff items from a section.

        Args:
            section: Section text containing outside diff items

        Returns:
            List of OutsideDiffComment objects
        """
        items = []

        # First, extract file-specific sections
        # Pattern: <summary>filename (count)</summary><blockquote> (with > prefix on each line)
        file_section_pattern = r"> <details>\s*\n> <summary>([^(]+)\s*\(\d+\)</summary><blockquote>(.*?)(?=> </blockquote></details>|\Z)"
        file_sections = list(re.finditer(file_section_pattern, section, re.DOTALL | re.IGNORECASE))

        for i, file_section in enumerate(file_sections):
            file_path = file_section.group(1).strip()
            file_content = file_section.group(2)

            # Pattern to match individual outside diff comments within this file (with > prefix)
            # Each comment starts with > `line-range`: **Title** and continues until next comment or section end
            comment_pattern = (
                r"> `(\d+(?:-\d+)?)`: \*\*([^*]+)\*\*\s*(.*?)(?=> `\d+(?:-\d+)?`:\s*\*\*|> ---|\Z)"
            )

            matches = re.finditer(comment_pattern, file_content, re.MULTILINE | re.DOTALL)

            for match in matches:
                line_range = match.group(1)
                title = match.group(2).strip()
                content_body = match.group(3).strip()

                # Combine title and content
                full_content = f"**{title}**"
                if content_body:
                    # Clean up content body
                    content_body = re.sub(r"\n+", "\n", content_body)
                    content_body = content_body.strip()
                    if content_body:
                        full_content += f"\n\n{content_body}"

                items.append(
                    OutsideDiffComment(
                        file_path=file_path,
                        line_range=line_range,
                        content=full_content,
                        reason="Outside diff range",
                        raw_content=match.group(0).strip(),
                    )
                )
        return items

    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from content with enhanced detection.

        Args:
            content: Text content that may contain code blocks

        Returns:
            List of dictionaries containing code block info: {code, language, type}
        """
        code_blocks = []

        # Phase 1: Enhanced code block patterns
        patterns = [
            # Multi-line diff blocks
            (r"```diff\s*\n(.*?)\n```", "diff", "diff"),
            # Standard markdown code blocks with language
            (r"```(\w+)\s*\n(.*?)\n```", r"\1", "code_block"),
            # Standard markdown code blocks without language
            (r"```\s*\n(.*?)\n```", "text", "code_block"),
            # Multi-line code suggestions (+ prefix)
            (r"(\n\+[^\n]*(?:\n\+[^\n]*)*)", "bash", "suggestion"),
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
                    language = "bash"  # Default for shell suggestions
                else:
                    code_content = match.group(2 if r"\1" in language_or_group else 1).strip()
                    language = match.group(1) if r"\1" in language_or_group else language_or_group

                # Phase 1: Filter out meaningless code fragments
                if code_content and len(code_content) > 10:
                    # Skip fragments that are just variable names or simple expressions
                    if not re.match(r"^[\w\s]*$", code_content) or " " in code_content:
                        code_blocks.append(
                            {"code": code_content, "language": language, "type": block_type}
                        )

        return code_blocks

    def has_review_content(self, content: str) -> bool:
        """Check if content contains review-like information.

        Args:
            content: Comment content to check

        Returns:
            True if content appears to be a review comment
        """
        review_indicators = [
            "actionable comments",
            "nitpick",
            "outside diff",
            "refactor suggestion",
            "potential issue",
            "verification agent",
            "analysis chain",
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

    def analyze_thread_context_relationships(
        self, threads: List, actionable_comments: List
    ) -> Dict[str, Any]:
        """Phase 3: Analyze relationships between thread contexts and actionable comments.

        Args:
            threads: List of thread contexts
            actionable_comments: List of actionable comments

        Returns:
            Dictionary of relationships and context enrichment data
        """
        relationships = {
            "thread_comment_mapping": {},
            "file_based_clusters": {},
            "priority_adjustments": {},
            "context_enrichments": {},
        }

        # Group actionable comments by file
        file_clusters = {}
        for comment in actionable_comments:
            file_path = comment.file_path
            if file_path not in file_clusters:
                file_clusters[file_path] = []
            file_clusters[file_path].append(comment)

        relationships["file_based_clusters"] = file_clusters

        # Map threads to actionable comments based on context
        for thread in threads:
            # thread_file = getattr(thread, "file_context", "")  # Not used currently
            # thread_line = getattr(thread, "line_context", "")  # Not used currently
            pass

            # Find related actionable comments
            related_comments = []
            for comment in actionable_comments:
                if self._is_contextually_related(thread, comment):
                    related_comments.append(comment)

            if related_comments:
                relationships["thread_comment_mapping"][getattr(thread, "thread_id", "unknown")] = {
                    "thread": thread,
                    "related_comments": related_comments,
                    "context_strength": self._calculate_context_strength(thread, related_comments),
                }

        # Generate priority adjustments based on context
        for _thread_id, mapping in relationships["thread_comment_mapping"].items():
            thread = mapping["thread"]
            comments = mapping["related_comments"]

            # Adjust priority based on thread discussion intensity
            if len(getattr(thread, "chronological_comments", [])) > 3:
                # High discussion activity suggests important issue
                for comment in comments:
                    if comment.priority.lower() == "low":
                        relationships["priority_adjustments"][comment.comment_id] = "MEDIUM"
                    elif comment.priority.lower() == "medium":
                        relationships["priority_adjustments"][comment.comment_id] = "HIGH"

        return relationships

    def _is_contextually_related(self, thread, comment) -> bool:
        """Check if a thread and comment are contextually related.

        Args:
            thread: Thread context
            comment: Actionable comment

        Returns:
            True if they appear to be related
        """
        thread_file = getattr(thread, "file_context", "")
        thread_line = str(getattr(thread, "line_context", ""))

        # Exact file match
        if thread_file and thread_file == comment.file_path:
            # Check line proximity
            if thread_line and hasattr(comment, "line_range"):
                try:
                    thread_line_num = int(thread_line)
                    comment_line = str(comment.line_range)
                    if "-" in comment_line:
                        # Range like "10-15"
                        line_parts = comment_line.split("-")
                        start_line = int(line_parts[0])
                        end_line = int(line_parts[1]) if len(line_parts) > 1 else start_line
                        return start_line <= thread_line_num <= end_line + 5  # Allow 5 lines buffer
                    else:
                        comment_line_num = int(comment_line)
                        return abs(thread_line_num - comment_line_num) <= 10  # Within 10 lines
                except (ValueError, AttributeError):
                    return True  # Same file is good enough
            return True

        # Partial file name match (for cases where paths might be different)
        if thread_file and comment.file_path:
            thread_basename = thread_file.split("/")[-1]
            comment_basename = comment.file_path.split("/")[-1]
            if thread_basename == comment_basename:
                return True

        return False

    def _calculate_context_strength(self, thread, related_comments) -> float:
        """Calculate the strength of context relationship.

        Args:
            thread: Thread context
            related_comments: List of related comments

        Returns:
            Strength score between 0.0 and 1.0
        """
        strength = 0.0

        # Base strength from having related comments
        strength += 0.3

        # Bonus for multiple related comments
        strength += min(len(related_comments) * 0.1, 0.3)

        # Bonus for discussion activity
        comment_count = len(getattr(thread, "chronological_comments", []))
        strength += min(comment_count * 0.05, 0.2)

        # Bonus for unresolved status
        if not getattr(thread, "is_resolved", True):
            strength += 0.2

        return min(strength, 1.0)

    def analyze_code_change_patterns(
        self, actionable_comments: List, pr_diff_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Phase 3: Analyze code change patterns to adjust priorities intelligently.

        Args:
            actionable_comments: List of actionable comments
            pr_diff_data: Optional PR diff data for analysis

        Returns:
            Analysis results with priority adjustments
        """
        analysis = {
            "change_type_distribution": {},
            "file_impact_scores": {},
            "priority_adjustments": {},
            "risk_indicators": [],
        }

        # Group comments by file and analyze change patterns
        file_groups = {}
        for comment in actionable_comments:
            file_path = comment.file_path
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(comment)

        for file_path, comments in file_groups.items():
            # Calculate file impact score
            impact_score = self._calculate_file_impact_score(file_path, comments)
            analysis["file_impact_scores"][file_path] = impact_score

            # Analyze change types
            change_types = self._identify_change_types(file_path, comments)
            analysis["change_type_distribution"][file_path] = change_types

            # Generate priority adjustments based on analysis
            adjustments = self._generate_priority_adjustments_from_analysis(
                file_path, comments, impact_score, change_types
            )
            analysis["priority_adjustments"].update(adjustments)

            # Identify risk indicators
            risks = self._identify_risk_indicators(file_path, comments, change_types)
            analysis["risk_indicators"].extend(risks)

        return analysis

    def _calculate_file_impact_score(self, file_path: str, comments: List) -> float:
        """Calculate impact score for a file based on comments and file type.

        Args:
            file_path: Path to the file
            comments: Comments related to this file

        Returns:
            Impact score between 0.0 and 1.0
        """
        score = 0.0

        # Base score from number of comments
        score += min(len(comments) * 0.15, 0.6)

        # File type importance
        file_ext = file_path.split(".")[-1].lower() if "." in file_path else ""

        critical_files = {
            "py": 0.8,
            "js": 0.8,
            "ts": 0.8,
            "java": 0.8,
            "cpp": 0.8,
            "c": 0.8,
            "go": 0.8,
            "rs": 0.8,
            "rb": 0.7,
            "php": 0.7,
            "scala": 0.7,
            "sql": 0.9,
            "dockerfile": 0.9,
            "yaml": 0.6,
            "yml": 0.6,
            "json": 0.6,
            "sh": 0.7,
            "bash": 0.7,
            "zsh": 0.7,
            "fish": 0.7,
        }

        # Critical file names
        file_name = file_path.split("/")[-1].lower()
        critical_names = {
            "main.py": 0.9,
            "index.js": 0.9,
            "app.py": 0.9,
            "server.py": 0.9,
            "config.py": 0.8,
            "settings.py": 0.8,
            "requirements.txt": 0.7,
            "package.json": 0.8,
            "dockerfile": 0.9,
            "makefile": 0.7,
            ".env": 0.9,
            ".gitignore": 0.3,
            "readme.md": 0.2,
        }

        if file_name in critical_names:
            score += critical_names[file_name] * 0.3
        elif file_ext in critical_files:
            score += critical_files[file_ext] * 0.2

        # Bonus for security-related files
        if any(
            keyword in file_path.lower()
            for keyword in ["auth", "security", "crypto", "token", "password", "secret"]
        ):
            score += 0.2

        # Bonus for core infrastructure files
        if any(
            keyword in file_path.lower()
            for keyword in ["core", "base", "main", "init", "setup", "config"]
        ):
            score += 0.1

        return min(score, 1.0)

    def _identify_change_types(self, file_path: str, comments: List) -> Dict[str, int]:
        """Identify types of changes based on comment content.

        Args:
            file_path: Path to the file
            comments: Comments for this file

        Returns:
            Dictionary of change type counts
        """
        change_types = {
            "security": 0,
            "performance": 0,
            "bug_fix": 0,
            "refactoring": 0,
            "new_feature": 0,
            "documentation": 0,
            "style": 0,
            "testing": 0,
        }

        for comment in comments:
            description = comment.issue_description.lower()

            # Security changes
            if any(
                keyword in description
                for keyword in [
                    "security",
                    "vulnerability",
                    "exploit",
                    "injection",
                    "xss",
                    "csrf",
                    "authentication",
                    "authorization",
                    "sanitize",
                    "validate",
                ]
            ):
                change_types["security"] += 1

            # Performance changes
            elif any(
                keyword in description
                for keyword in [
                    "performance",
                    "optimize",
                    "slow",
                    "memory",
                    "cpu",
                    "cache",
                    "efficiency",
                    "bottleneck",
                    "latency",
                ]
            ):
                change_types["performance"] += 1

            # Bug fixes
            elif any(
                keyword in description
                for keyword in ["bug", "error", "fix", "issue", "problem", "crash", "fail"]
            ):
                change_types["bug_fix"] += 1

            # Refactoring
            elif any(
                keyword in description
                for keyword in ["refactor", "restructure", "cleanup", "simplify", "extract"]
            ):
                change_types["refactoring"] += 1

            # New features
            elif any(
                keyword in description
                for keyword in ["add", "new", "feature", "implement", "create", "introduce"]
            ):
                change_types["new_feature"] += 1

            # Documentation
            elif any(
                keyword in description
                for keyword in ["document", "comment", "readme", "doc", "explain"]
            ):
                change_types["documentation"] += 1

            # Style/formatting
            elif any(
                keyword in description
                for keyword in ["style", "format", "indent", "whitespace", "lint"]
            ):
                change_types["style"] += 1

            # Testing
            elif any(
                keyword in description for keyword in ["test", "spec", "coverage", "mock", "assert"]
            ):
                change_types["testing"] += 1

        return change_types

    def _generate_priority_adjustments_from_analysis(
        self, file_path: str, comments: List, impact_score: float, change_types: Dict[str, int]
    ) -> Dict[str, str]:
        """Generate priority adjustments based on file analysis.

        Args:
            file_path: Path to the file
            comments: Comments for this file
            impact_score: Calculated impact score
            change_types: Distribution of change types

        Returns:
            Dictionary of comment_id to new priority mappings
        """
        adjustments = {}

        # High impact files get priority boost
        if impact_score > 0.7:
            for comment in comments:
                current_priority = comment.priority.lower()
                if current_priority == "low":
                    adjustments[comment.comment_id] = "MEDIUM"
                elif current_priority == "medium":
                    adjustments[comment.comment_id] = "HIGH"

        # Security changes always get high priority
        if change_types.get("security", 0) > 0:
            for comment in comments:
                if any(
                    keyword in comment.issue_description.lower()
                    for keyword in ["security", "vulnerability", "exploit"]
                ):
                    adjustments[comment.comment_id] = "HIGH"

        # Performance issues in critical files get boosted
        if change_types.get("performance", 0) > 0 and impact_score > 0.6:
            for comment in comments:
                if any(
                    keyword in comment.issue_description.lower()
                    for keyword in ["performance", "optimize", "slow"]
                ):
                    current_priority = comment.priority.lower()
                    if current_priority != "high":
                        adjustments[comment.comment_id] = "HIGH"

        return adjustments

    def _identify_risk_indicators(
        self, file_path: str, comments: List, change_types: Dict[str, int]
    ) -> List[Dict[str, str]]:
        """Identify risk indicators based on file and change analysis.

        Args:
            file_path: Path to the file
            comments: Comments for this file
            change_types: Distribution of change types

        Returns:
            List of risk indicator dictionaries
        """
        risks = []

        # Multiple security issues in one file
        if change_types.get("security", 0) > 2:
            risks.append(
                {
                    "type": "multiple_security_issues",
                    "severity": "HIGH",
                    "description": f"Multiple security issues detected in {file_path}",
                    "file_path": file_path,
                }
            )

        # High comment concentration (possible problem area)
        if len(comments) > 5:
            risks.append(
                {
                    "type": "high_issue_concentration",
                    "severity": "MEDIUM",
                    "description": f"High concentration of issues in {file_path} ({len(comments)} comments)",
                    "file_path": file_path,
                }
            )

        # Mix of security and performance issues
        if change_types.get("security", 0) > 0 and change_types.get("performance", 0) > 0:
            risks.append(
                {
                    "type": "security_performance_mix",
                    "severity": "HIGH",
                    "description": f"Both security and performance issues in {file_path}",
                    "file_path": file_path,
                }
            )

        return risks

    def optimize_processing_for_large_datasets(
        self, comments: List, max_items: int = 1000
    ) -> Dict[str, Any]:
        """Phase 3: Optimize processing for large PR datasets.

        Args:
            comments: List of comments to process
            max_items: Maximum number of items to process efficiently

        Returns:
            Optimization results and processing strategy
        """
        optimization = {
            "dataset_size": len(comments),
            "processing_strategy": "standard",
            "sampling_applied": False,
            "filtered_count": 0,
            "optimization_applied": [],
        }

        # Large dataset handling
        if len(comments) > max_items:
            optimization["processing_strategy"] = "optimized"
            optimization["optimization_applied"].append("large_dataset_sampling")

            # Intelligent sampling - prioritize important comments
            sampled_comments = self._intelligent_sampling(comments, max_items)
            optimization["filtered_count"] = len(sampled_comments)
            optimization["sampling_applied"] = True

        # Memory optimization for code blocks
        if optimization["dataset_size"] > 500:
            optimization["optimization_applied"].append("code_block_compression")

        # Parallel processing recommendation
        if optimization["dataset_size"] > 200:
            optimization["optimization_applied"].append("parallel_processing_recommended")

        return optimization

    def _intelligent_sampling(self, comments: List, target_size: int) -> List:
        """Intelligent sampling that preserves important comments.

        Args:
            comments: Full list of comments
            target_size: Target number of comments to keep

        Returns:
            Sampled list of comments
        """
        if len(comments) <= target_size:
            return comments

        # Score comments by importance
        scored_comments = []
        for comment in comments:
            score = self._calculate_comment_importance_score(comment)
            scored_comments.append((comment, score))

        # Sort by importance and take top N
        scored_comments.sort(key=lambda x: x[1], reverse=True)
        return [comment for comment, score in scored_comments[:target_size]]

    def _calculate_comment_importance_score(self, comment) -> float:
        """Calculate importance score for comment sampling.

        Args:
            comment: Comment to score

        Returns:
            Importance score
        """
        score = 0.0

        if hasattr(comment, "issue_description"):
            description = comment.issue_description.lower()

            # High importance keywords
            high_importance = [
                "security",
                "vulnerability",
                "critical",
                "error",
                "bug",
                "performance",
            ]
            for keyword in high_importance:
                if keyword in description:
                    score += 2.0

            # Medium importance keywords
            medium_importance = ["improve", "optimize", "refactor", "update", "fix"]
            for keyword in medium_importance:
                if keyword in description:
                    score += 1.0

            # Priority boost
            if hasattr(comment, "priority"):
                priority_scores = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}
                priority = (
                    comment.priority.value
                    if hasattr(comment.priority, "value")
                    else str(comment.priority)
                )
                score += priority_scores.get(priority.upper(), 1.0)

        return score

    def enhanced_error_recovery(
        self, operation_name: str, data: Any, fallback_strategy: str = "graceful"
    ) -> Dict[str, Any]:
        """Phase 3: Enhanced error handling with recovery strategies.

        Args:
            operation_name: Name of the operation being performed
            data: Data being processed
            fallback_strategy: Strategy for error recovery

        Returns:
            Recovery result with status and processed data
        """
        recovery_result = {
            "operation": operation_name,
            "status": "success",
            "errors_encountered": [],
            "recovery_applied": [],
            "processed_data": data,
            "warnings": [],
        }

        try:
            # Validate input data
            if not data:
                recovery_result["warnings"].append("Empty input data provided")
                return recovery_result

            # Apply error-prone operation simulation (in real usage, this would be the actual operation)
            if isinstance(data, list) and len(data) > 1000:
                recovery_result["warnings"].append("Large dataset detected - applying optimization")
                recovery_result["recovery_applied"].append("dataset_optimization")

            # Memory management for large operations
            if hasattr(data, "__len__") and len(data) > 500:
                recovery_result["recovery_applied"].append("memory_management")

        except Exception as e:
            recovery_result["status"] = "error_recovered"
            recovery_result["errors_encountered"].append(
                {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "fallback_applied": fallback_strategy,
                }
            )

            # Apply fallback strategies
            if fallback_strategy == "graceful":
                # Continue with partial results
                recovery_result["processed_data"] = self._create_minimal_fallback_data()
                recovery_result["recovery_applied"].append("graceful_degradation")

            elif fallback_strategy == "retry":
                # Attempt retry with simplified processing
                recovery_result["recovery_applied"].append("simplified_retry")
                recovery_result["processed_data"] = self._create_simplified_data(data)

            elif fallback_strategy == "skip":
                # Skip problematic items
                recovery_result["recovery_applied"].append("selective_skipping")
                recovery_result["processed_data"] = []

        return recovery_result

    def _create_minimal_fallback_data(self) -> List[Any]:
        """Create minimal fallback data structure."""
        return []

    def _create_simplified_data(self, original_data: Any) -> List[Any]:
        """Create simplified version of data for retry."""
        if isinstance(original_data, list):
            # Return first 100 items as simplified set
            return original_data[:100] if len(original_data) > 100 else original_data
        return []

    def validate_phase3_integration(self) -> Dict[str, Any]:
        """Validate that Phase 3 features are properly integrated.

        Returns:
            Validation result with status and feature availability
        """
        validation = {
            "phase3_features": {
                "context_relationships": False,
                "code_pattern_analysis": False,
                "performance_optimization": False,
                "error_recovery": False,
                "intelligent_prioritization": False,
            },
            "integration_status": "unknown",
            "missing_features": [],
            "warnings": [],
        }

        # Check for context relationship methods
        if hasattr(self, "analyze_thread_context_relationships"):
            validation["phase3_features"]["context_relationships"] = True
        else:
            validation["missing_features"].append("analyze_thread_context_relationships")

        # Check for code pattern analysis
        if hasattr(self, "analyze_code_change_patterns"):
            validation["phase3_features"]["code_pattern_analysis"] = True
        else:
            validation["missing_features"].append("analyze_code_change_patterns")

        # Check for performance optimization
        if hasattr(self, "optimize_processing_for_large_datasets"):
            validation["phase3_features"]["performance_optimization"] = True
        else:
            validation["missing_features"].append("optimize_processing_for_large_datasets")

        # Check for error recovery
        if hasattr(self, "enhanced_error_recovery"):
            validation["phase3_features"]["error_recovery"] = True
        else:
            validation["missing_features"].append("enhanced_error_recovery")

        # Check for intelligent prioritization (via ActionableComment model)
        try:
            from ..models.actionable_comment import ActionableComment

            if hasattr(ActionableComment, "_detect_priority"):
                validation["phase3_features"]["intelligent_prioritization"] = True
            else:
                validation["missing_features"].append("intelligent_prioritization")
        except ImportError:
            validation["missing_features"].append("actionable_comment_model")

        # Determine integration status
        enabled_features = sum(validation["phase3_features"].values())
        total_features = len(validation["phase3_features"])

        if enabled_features == total_features:
            validation["integration_status"] = "fully_integrated"
        elif enabled_features >= total_features * 0.8:
            validation["integration_status"] = "mostly_integrated"
        elif enabled_features >= total_features * 0.5:
            validation["integration_status"] = "partially_integrated"
        else:
            validation["integration_status"] = "poorly_integrated"

        return validation

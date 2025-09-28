"""Plain text formatter for CodeRabbit comment output."""

from typing import List
from datetime import datetime

from .base_formatter import BaseFormatter
from ..models import (
    AnalyzedComments,
    SummaryComment,
    ReviewComment,
    ThreadContext,
    AIAgentPrompt,
    ActionableComment,
    NitpickComment,
    OutsideDiffComment
)


class PlainTextFormatter(BaseFormatter):
    """Plain text formatter for simple, readable CodeRabbit comment output."""

    def __init__(self, line_width: int = 80, include_separators: bool = True):
        """Initialize plain text formatter.

        Args:
            line_width: Maximum line width for text wrapping
            include_separators: Whether to include section separators
        """
        super().__init__()
        self.line_width = line_width
        self.include_separators = include_separators

    def format(self, persona: str, analyzed_comments: AnalyzedComments) -> str:
        """Format analyzed comments as plain text.

        Args:
            persona: AI persona prompt string
            analyzed_comments: Analyzed CodeRabbit comments

        Returns:
            Formatted plain text string
        """
        sections = []

        # Title and header
        sections.append("CODERABBIT ANALYSIS REPORT")
        sections.append("=" * self.line_width)
        sections.append("")

        # Timestamp
        sections.append(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append("")

        # Persona section (condensed)
        sections.append("AI ASSISTANT PERSONA")
        sections.append("-" * 20)
        sections.append(self._format_persona_condensed(persona))
        sections.append("")

        if self.include_separators:
            sections.append("=" * self.line_width)
            sections.append("")

        # Summary section
        if analyzed_comments.summary_comments:
            sections.append("SUMMARY ANALYSIS")
            sections.append("-" * 16)
            for summary in analyzed_comments.summary_comments:
                sections.append(self.format_summary_section(summary))
            sections.append("")

        # Review comments section
        if analyzed_comments.review_comments:
            sections.append("DETAILED REVIEW COMMENTS")
            sections.append("-" * 24)
            for i, review in enumerate(analyzed_comments.review_comments, 1):
                sections.append(f"Review Comment #{i}")
                sections.append(self.format_review_section(review))
                sections.append("")

        # Thread contexts section
        if analyzed_comments.unresolved_threads:
            sections.append("THREAD DISCUSSIONS")
            sections.append("-" * 18)
            for i, thread in enumerate(analyzed_comments.unresolved_threads, 1):
                sections.append(f"Thread #{i}")
                sections.append(self.format_thread_section(thread))
                sections.append("")

        # Footer with metadata
        if self.include_separators:
            sections.append("=" * self.line_width)

        metadata = self.format_metadata(analyzed_comments)
        sections.append("REPORT STATISTICS")
        sections.append("-" * 17)
        sections.append(f"Total Comments: {metadata['total_comments']}")
        sections.append(f"Summary Comments: {metadata['summary_count']}")
        sections.append(f"Review Comments: {metadata['review_count']}")
        sections.append(f"Thread Discussions: {metadata['total_threads']}")
        sections.append(f"Formatter: {metadata['formatter_type']}")

        return "\n".join(sections)

    def format_summary_section(self, summary: SummaryComment) -> str:
        """Format summary comment section as plain text.

        Args:
            summary: Summary comment to format

        Returns:
            Formatted summary section
        """
        sections = []

        # Main walkthrough
        if summary.walkthrough:
            sections.append("Summary:")
            sections.append(self._wrap_text(summary.walkthrough))
            sections.append("")

        # Statistics
        sections.append("Statistics:")
        sections.append(f"  - Total Changes: {summary.total_changes}")
        sections.append("")

        # New features
        if summary.new_features:
            sections.append("New Features:")
            for feature in summary.new_features:
                sections.append(f"  - {self._wrap_text(feature, indent=4)}")
            sections.append("")

        # Documentation changes
        if summary.documentation_changes:
            sections.append("Documentation Changes:")
            for doc_change in summary.documentation_changes:
                sections.append(f"  - {self._wrap_text(doc_change, indent=4)}")
            sections.append("")

        # Test changes
        if summary.test_changes:
            sections.append("Test Changes:")
            for test_change in summary.test_changes:
                sections.append(f"  - {self._wrap_text(test_change, indent=4)}")
            sections.append("")

        return "\n".join(sections)

    def format_review_section(self, review: ReviewComment) -> str:
        """Format review comment section as plain text.

        Args:
            review: Review comment to format

        Returns:
            Formatted review section
        """
        sections = []

        # Actionable comments
        if review.actionable_comments:
            sections.append("ACTIONABLE ITEMS:")
            sections.append(self.format_actionable_comments(review.actionable_comments))

        # Nitpick comments
        if review.nitpick_comments:
            sections.append("CODE STYLE & QUALITY:")
            sections.append(self.format_nitpick_comments(review.nitpick_comments))

        # Outside diff comments
        if review.outside_diff_comments:
            sections.append("OUTSIDE DIFF RANGE:")
            sections.append(self.format_outside_diff_comments(review.outside_diff_comments))

        # AI Agent prompts
        if review.ai_agent_prompts:
            sections.append("AI AGENT PROMPTS:")
            for i, prompt in enumerate(review.ai_agent_prompts, 1):
                sections.append(f"  {i}. {self.format_ai_agent_prompt(prompt)}")
                sections.append("")

        return "\n".join(sections)

    def format_thread_section(self, thread: ThreadContext) -> str:
        """Format thread context section as plain text.

        Args:
            thread: Thread context to format

        Returns:
            Formatted thread section
        """
        sections = []

        # Thread info
        thread_id = getattr(thread, 'thread_id', 'Unknown')
        sections.append(f"Thread ID: {thread_id}")
        sections.append(f"Status: {thread.resolution_status}")

        if hasattr(thread, 'file_context') and thread.file_context:
            sections.append(f"File: {thread.file_context}")

        if hasattr(thread, 'line_context') and thread.line_context:
            sections.append(f"Line: {thread.line_context}")

        if hasattr(thread, 'participants') and thread.participants:
            participants = ", ".join(thread.participants)
            sections.append(f"Participants: {participants}")

        if hasattr(thread, 'comment_count'):
            sections.append(f"Comments: {thread.comment_count}")

        sections.append("")

        # AI Summary or contextual summary
        if hasattr(thread, 'ai_summary') and thread.ai_summary:
            sections.append("AI Analysis:")
            sections.append(self._wrap_text(thread.ai_summary))
        elif thread.contextual_summary:
            sections.append("Summary:")
            sections.append(self._wrap_text(thread.contextual_summary))

        sections.append("")

        # Discussion timeline
        if thread.chronological_order:
            sections.append("Discussion Timeline:")
            for i, comment in enumerate(thread.chronological_order, 1):
                content = self._extract_comment_content_safe(comment)
                wrapped_content = self._wrap_text(content, max_length=200)
                sections.append(f"  {i}. {wrapped_content}")
            sections.append("")

        return "\n".join(sections)

    def format_ai_agent_prompt(self, prompt: AIAgentPrompt) -> str:
        """Format AI agent prompt as plain text.

        Args:
            prompt: AI agent prompt to format

        Returns:
            Formatted AI agent prompt
        """
        sections = []

        # Description
        if prompt.description:
            sections.append(f"Description: {prompt.description}")

        # File and line info
        if prompt.file_path:
            sections.append(f"File: {prompt.file_path}")

        if prompt.line_range:
            sections.append(f"Lines: {prompt.line_range}")

        # Code block (truncated for plain text)
        if prompt.code_block:
            code_preview = self._truncate_content(prompt.code_block, 100)
            sections.append(f"Code: {code_preview}")

        # Completion status
        if hasattr(prompt, 'is_complete_suggestion') and prompt.is_complete_suggestion:
            sections.append("Status: Complete implementation")
        else:
            sections.append("Status: Partial guidance")

        return "\n     ".join(sections)  # Indent continuation lines

    def format_actionable_comments(self, comments: List[ActionableComment]) -> str:
        """Format actionable comments as plain text.

        Args:
            comments: List of actionable comments

        Returns:
            Formatted actionable comments
        """
        if not comments:
            return "  (No actionable items)"

        sections = []
        for i, comment in enumerate(comments, 1):
            priority = self._extract_priority_level(comment.description or "")
            priority_marker = {"High": "[HIGH]", "Medium": "[MED]", "Low": "[LOW]"}.get(priority, "")

            header = f"  {i}. {priority_marker} {comment.title}"
            sections.append(header)

            if comment.description:
                wrapped_desc = self._wrap_text(comment.description, indent=6)
                sections.append(f"     {wrapped_desc}")

            # Location
            location_parts = []
            if comment.file_path:
                location_parts.append(comment.file_path)
            if comment.line_number:
                location_parts.append(f"Line {comment.line_number}")

            if location_parts:
                sections.append(f"     Location: {' - '.join(location_parts)}")

            sections.append("")

        return "\n".join(sections)

    def format_nitpick_comments(self, comments: List[NitpickComment]) -> str:
        """Format nitpick comments as plain text.

        Args:
            comments: List of nitpick comments

        Returns:
            Formatted nitpick comments
        """
        if not comments:
            return "  (No nitpick comments)"

        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"  {i}. {comment.suggestion}")

            # Location
            location_parts = []
            if comment.file_path:
                location_parts.append(comment.file_path)
            if comment.line_number:
                location_parts.append(f"Line {comment.line_number}")

            if location_parts:
                sections.append(f"     Location: {' - '.join(location_parts)}")

            sections.append("")

        return "\n".join(sections)

    def format_outside_diff_comments(self, comments: List[OutsideDiffComment]) -> str:
        """Format outside diff comments as plain text.

        Args:
            comments: List of outside diff comments

        Returns:
            Formatted outside diff comments
        """
        if not comments:
            return "  (No outside diff comments)"

        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"  {i}. {comment.issue}")

            if comment.description:
                wrapped_desc = self._wrap_text(comment.description, indent=6)
                sections.append(f"     {wrapped_desc}")

            # Location
            location_parts = []
            if comment.file_path:
                location_parts.append(comment.file_path)
            if comment.line_range:
                location_parts.append(f"Lines {comment.line_range}")

            if location_parts:
                sections.append(f"     Location: {' - '.join(location_parts)}")

            sections.append("")

        return "\n".join(sections)

    def _format_persona_condensed(self, persona: str) -> str:
        """Format persona in condensed form for plain text.

        Args:
            persona: Persona string to format

        Returns:
            Condensed persona description
        """
        # Extract key information from persona
        lines = persona.split('\n')
        key_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Look for role definition
            if any(keyword in line.lower() for keyword in ['you are', 'role', 'expert', 'specialist']):
                key_lines.append(line)
                if len(key_lines) >= 2:  # Limit to keep it condensed
                    break

        if key_lines:
            return self._wrap_text(' '.join(key_lines))
        else:
            # Fallback to first non-empty, non-header line
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 20:
                    return self._wrap_text(line)

            return "AI assistant for CodeRabbit comment analysis"

    def _wrap_text(self, text: str, indent: int = 0, max_length: int = None) -> str:
        """Wrap text to fit line width.

        Args:
            text: Text to wrap
            indent: Number of spaces to indent continuation lines
            max_length: Maximum length before truncation

        Returns:
            Wrapped text string
        """
        if not text:
            return ""

        # Truncate if too long
        if max_length and len(text) > max_length:
            text = text[:max_length-3] + "..."

        # Clean and sanitize
        text = self._sanitize_content(text)

        # Simple word wrapping
        available_width = self.line_width - indent
        if available_width <= 20:  # Prevent too narrow wrapping
            available_width = 40

        words = text.split()
        if not words:
            return ""

        lines = []
        current_line = words[0]

        for word in words[1:]:
            if len(current_line) + len(word) + 1 <= available_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = " " * indent + word

        lines.append(current_line)
        return "\n".join(lines)

    def _extract_comment_content_safe(self, comment) -> str:
        """Safely extract content from comment object.

        Args:
            comment: Comment object to extract content from

        Returns:
            Comment content string
        """
        try:
            if hasattr(comment, 'body'):
                return comment.body or ""
            elif hasattr(comment, 'content'):
                return comment.content or ""
            elif isinstance(comment, str):
                return comment
            else:
                return str(comment)
        except Exception:
            return "[Comment content unavailable]"

"""Markdown formatter for CodeRabbit comment output."""

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


class MarkdownFormatter(BaseFormatter):
    """Markdown formatter for CodeRabbit comments with proper structure."""
    
    def __init__(self, include_metadata: bool = True, include_toc: bool = True):
        """Initialize markdown formatter.
        
        Args:
            include_metadata: Whether to include metadata section
            include_toc: Whether to include table of contents
        """
        super().__init__()
        self.include_metadata = include_metadata
        self.include_toc = include_toc
        self.visual_markers = self.get_visual_markers()
    
    def format(self, persona: str, analyzed_comments: AnalyzedComments) -> str:
        """Format analyzed comments as Markdown.
        
        Args:
            persona: AI persona prompt string
            analyzed_comments: Analyzed CodeRabbit comments
            
        Returns:
            Formatted Markdown string
        """
        sections = []
        
        # Title and Persona
        sections.append("# CodeRabbit Analysis Report")
        sections.append("")
        sections.append("## AI Assistant Persona")
        sections.append(self._format_persona_block(persona))
        sections.append("")
        
        # Table of Contents
        if self.include_toc:
            sections.append(self._generate_table_of_contents(analyzed_comments))
            sections.append("")
        
        # Summary Section
        if analyzed_comments.summary_comments:
            sections.append("## 📊 Summary Analysis")
            for summary in analyzed_comments.summary_comments:
                sections.append(self.format_summary_section(summary))
            sections.append("")
        
        # Review Comments Section
        if analyzed_comments.review_comments:
            sections.append("## 🔍 Detailed Review Comments")
            for review in analyzed_comments.review_comments:
                sections.append(self.format_review_section(review))
            sections.append("")
        
        # Thread Contexts Section
        if analyzed_comments.unresolved_threads:
            sections.append("## 💬 Thread Discussions")
            for thread in analyzed_comments.unresolved_threads:
                sections.append(self.format_thread_section(thread))
            sections.append("")
        
        # Metadata Section
        if self.include_metadata:
            sections.append(self._format_metadata_section(analyzed_comments))
        
        return "\n".join(sections)
    
    def format_summary_section(self, summary: SummaryComment) -> str:
        """Format summary comment section.
        
        Args:
            summary: Summary comment to format
            
        Returns:
            Formatted summary section
        """
        sections = []
        
        sections.append("### Summary Overview")
        
        # Main walkthrough content
        if summary.walkthrough:
            sections.append("#### Summary")
            sections.append(summary.walkthrough)
            sections.append("")
        
        # Statistics
        sections.append("#### Statistics")
        sections.append(f"- **Total Changes**: {summary.total_changes}")
        sections.append("")
        
        # New features
        if summary.new_features:
            sections.append("#### New Features")
            for feature in summary.new_features:
                sections.append(f"- {feature}")
            sections.append("")
        
        # Documentation changes
        if summary.documentation_changes:
            sections.append("#### Documentation Changes")
            for doc_change in summary.documentation_changes:
                sections.append(f"- {doc_change}")
            sections.append("")
        
        # Test changes
        if summary.test_changes:
            sections.append("#### Test Changes")
            for test_change in summary.test_changes:
                sections.append(f"- {test_change}")
            sections.append("")
        
        # Changes table
        if summary.changes_table:
            sections.append("#### Changes Table")
            for change in summary.changes_table:
                sections.append(f"- **{change.cohort_or_files}**: {change.summary}")
            sections.append("")
        
        return "\n".join(sections)
    
    def format_review_section(self, review: ReviewComment) -> str:
        """Format review comment section.
        
        Args:
            review: Review comment to format
            
        Returns:
            Formatted review section
        """
        sections = []
        
        # Section header with visual distinction
        comment_type = self._determine_comment_type(review)
        marker = self.visual_markers.get(comment_type, "💬")
        sections.append(f"### {marker} Review Comment")
        sections.append("")
        
        # Actionable comments
        if review.actionable_comments:
            sections.append(f"#### {self.visual_markers['actionable']} Actionable Items")
            sections.append(self.format_actionable_comments(review.actionable_comments))
        
        # Nitpick comments
        if review.nitpick_comments:
            sections.append(f"#### {self.visual_markers['nitpick']} Code Style & Quality")
            sections.append(self.format_nitpick_comments(review.nitpick_comments))
        
        # Outside diff comments
        if review.outside_diff_comments:
            sections.append(f"#### {self.visual_markers['outside_diff']} Outside Diff Range")
            sections.append(self.format_outside_diff_comments(review.outside_diff_comments))
        
        # AI Agent prompts with special formatting
        if review.ai_agent_prompts:
            sections.append(f"#### {self.visual_markers['ai_prompt']} AI Agent Prompts")
            for prompt in review.ai_agent_prompts:
                sections.append(self.format_ai_agent_prompt(prompt))
                sections.append("")
        
        # Raw content as collapsible section
        if review.raw_content:
            sections.append("<details>")
            sections.append("<summary>📄 View Raw Comment Content</summary>")
            sections.append("")
            sections.append("```")
            sections.append(self._sanitize_content(review.raw_content))
            sections.append("```")
            sections.append("</details>")
            sections.append("")
        
        return "\n".join(sections)
    
    def format_thread_section(self, thread: ThreadContext) -> str:
        """Format thread context section.
        
        Args:
            thread: Thread context to format
            
        Returns:
            Formatted thread section
        """
        sections = []
        
        # Thread header
        thread_id = getattr(thread, 'thread_id', 'Unknown')
        sections.append(f"### 🧵 Thread: {thread_id}")
        sections.append("")
        
        # Thread metadata
        sections.append("#### Thread Information")
        sections.append(f"- **Status**: {thread.resolution_status}")
        
        if hasattr(thread, 'file_context') and thread.file_context:
            sections.append(f"- **File**: `{thread.file_context}`")
        
        if hasattr(thread, 'line_context') and thread.line_context:
            sections.append(f"- **Line**: {thread.line_context}")
        
        if hasattr(thread, 'participants') and thread.participants:
            participants = ", ".join([f"`{p}`" for p in thread.participants])
            sections.append(f"- **Participants**: {participants}")
        
        if hasattr(thread, 'comment_count'):
            sections.append(f"- **Comment Count**: {thread.comment_count}")
        
        sections.append("")
        
        # AI Summary with structured format
        if hasattr(thread, 'ai_summary') and thread.ai_summary:
            sections.append("#### 🤖 AI Analysis")
            sections.append(thread.ai_summary)
            sections.append("")
        
        # Contextual summary (fallback)
        elif thread.contextual_summary:
            sections.append("#### Summary")
            sections.append(thread.contextual_summary)
            sections.append("")
        
        # Chronological comments
        if thread.chronological_order:
            sections.append("#### 📝 Discussion Timeline")
            for i, comment in enumerate(thread.chronological_order, 1):
                sections.append(f"**{i}.** {self._format_timeline_comment(comment)}")
                sections.append("")
        
        return "\n".join(sections)
    
    def format_ai_agent_prompt(self, prompt: AIAgentPrompt) -> str:
        """Format AI agent prompt with special Markdown handling.
        
        Args:
            prompt: AI agent prompt to format
            
        Returns:
            Formatted AI agent prompt
        """
        sections = []
        
        # Prompt header with icon
        sections.append(f"##### {self.visual_markers['ai_prompt']} AI Agent Prompt")
        
        # Description
        if prompt.description:
            sections.append(f"**Description**: {prompt.description}")
            sections.append("")
        
        # File and line information
        if prompt.file_path:
            sections.append(f"**File**: `{prompt.file_path}`")
        
        if prompt.line_range:
            sections.append(f"**Lines**: {prompt.line_range}")
        
        if prompt.file_path or prompt.line_range:
            sections.append("")
        
        # Code block with language detection
        if prompt.code_block:
            language = getattr(prompt, 'language', '') or self._detect_language(prompt.code_block)
            sections.append("**Suggested Code**:")
            sections.append(f"```{language}")
            sections.append(prompt.code_block)
            sections.append("```")
        
        # Completion status
        if hasattr(prompt, 'is_complete_suggestion') and prompt.is_complete_suggestion:
            sections.append("✅ *Complete implementation suggestion*")
        else:
            sections.append("📝 *Partial guidance*")
        
        return "\n".join(sections)
    
    def format_actionable_comments(self, comments: List[ActionableComment]) -> str:
        """Format actionable comments with Markdown styling.
        
        Args:
            comments: List of actionable comments
            
        Returns:
            Formatted actionable comments
        """
        if not comments:
            return "*No actionable items*"
        
        sections = []
        for i, comment in enumerate(comments, 1):
            priority = self._extract_priority_level(comment.description or "")
            priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
            
            sections.append(f"{i}. {priority_icon} **{comment.title}**")
            
            if comment.description:
                sections.append(f"   {comment.description}")
            
            # Location info
            location_parts = []
            if comment.file_path:
                location_parts.append(f"`{comment.file_path}`")
            if comment.line_number:
                location_parts.append(f"Line {comment.line_number}")
            
            if location_parts:
                sections.append(f"   📍 {' - '.join(location_parts)}")
            
            sections.append("")
        
        return "\n".join(sections)
    
    def format_nitpick_comments(self, comments: List[NitpickComment]) -> str:
        """Format nitpick comments with Markdown styling.
        
        Args:
            comments: List of nitpick comments
            
        Returns:
            Formatted nitpick comments
        """
        if not comments:
            return "*No nitpick comments*"
        
        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"{i}. {comment.suggestion}")
            
            # Location info
            location_parts = []
            if comment.file_path:
                location_parts.append(f"`{comment.file_path}`")
            if comment.line_number:
                location_parts.append(f"Line {comment.line_number}")
            
            if location_parts:
                sections.append(f"   📍 {' - '.join(location_parts)}")
            
            sections.append("")
        
        return "\n".join(sections)
    
    def format_outside_diff_comments(self, comments: List[OutsideDiffComment]) -> str:
        """Format outside diff comments with Markdown styling.
        
        Args:
            comments: List of outside diff comments
            
        Returns:
            Formatted outside diff comments
        """
        if not comments:
            return "*No outside diff comments*"
        
        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"{i}. ⚠️ **{comment.issue}**")
            
            if comment.description:
                sections.append(f"   {comment.description}")
            
            # Location info
            location_parts = []
            if comment.file_path:
                location_parts.append(f"`{comment.file_path}`")
            if comment.line_range:
                location_parts.append(f"Lines {comment.line_range}")
            
            if location_parts:
                sections.append(f"   📍 {' - '.join(location_parts)}")
            
            sections.append("")
        
        return "\n".join(sections)
    
    def _format_persona_block(self, persona: str) -> str:
        """Format persona as a readable block.
        
        Args:
            persona: Persona string to format
            
        Returns:
            Formatted persona block
        """
        # Use collapsible section for long personas
        if len(persona) > 500:
            return f"""<details>
<summary>🎭 Click to view AI Assistant Persona</summary>

{persona}

</details>"""
        else:
            return f"```\n{persona}\n```"
    
    def _generate_table_of_contents(self, analyzed_comments: AnalyzedComments) -> str:
        """Generate table of contents.
        
        Args:
            analyzed_comments: Analyzed comments to generate TOC for
            
        Returns:
            Table of contents string
        """
        sections = ["## 📋 Table of Contents"]
        
        if analyzed_comments.summary_comments:
            sections.append("- [📊 Summary Analysis](#-summary-analysis)")
        
        if analyzed_comments.review_comments:
            sections.append("- [🔍 Detailed Review Comments](#-detailed-review-comments)")
        
        if analyzed_comments.unresolved_threads:
            sections.append("- [💬 Thread Discussions](#-thread-discussions)")
        
        if self.include_metadata:
            sections.append("- [📈 Report Metadata](#-report-metadata)")
        
        return "\n".join(sections)
    
    def _format_metadata_section(self, analyzed_comments: AnalyzedComments) -> str:
        """Format metadata section.
        
        Args:
            analyzed_comments: Analyzed comments for metadata
            
        Returns:
            Formatted metadata section
        """
        metadata = self.format_metadata(analyzed_comments)
        
        sections = []
        sections.append("## 📈 Report Metadata")
        sections.append("")
        sections.append(f"- **Generated**: {datetime.fromisoformat(metadata['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"- **Formatter**: {metadata['formatter_type']}")
        sections.append(f"- **Total Comments**: {metadata['total_comments']}")
        sections.append(f"- **Summary Comments**: {metadata['summary_count']}")
        sections.append(f"- **Review Comments**: {metadata['review_count']}")
        sections.append(f"- **Thread Discussions**: {metadata['total_threads']}")
        
        return "\n".join(sections)
    
    def _format_timeline_comment(self, comment) -> str:
        """Format a single timeline comment.
        
        Args:
            comment: Comment object to format
            
        Returns:
            Formatted timeline comment
        """
        # Handle different comment formats
        if hasattr(comment, 'body'):
            content = comment.body
        elif hasattr(comment, 'content'):
            content = comment.content
        elif isinstance(comment, str):
            content = comment
        else:
            content = str(comment)
        
        # Truncate long content
        content = self._truncate_content(content, 200)
        content = self._sanitize_content(content)
        
        return content
    
    def _determine_comment_type(self, review: ReviewComment) -> str:
        """Determine the primary type of a review comment.
        
        Args:
            review: Review comment to analyze
            
        Returns:
            Comment type string
        """
        if review.ai_agent_prompts:
            return "ai_prompt"
        elif review.actionable_comments:
            # Check for security/performance indicators
            content = " ".join([c.description or "" for c in review.actionable_comments])
            if "security" in content.lower() or "vulnerability" in content.lower():
                return "security"
            elif "performance" in content.lower() or "optimize" in content.lower():
                return "performance"
            else:
                return "actionable"
        elif review.nitpick_comments:
            return "nitpick"
        elif review.outside_diff_comments:
            return "outside_diff"
        else:
            return "general"
    
    def _detect_language(self, code_block: str) -> str:
        """Detect programming language from code block.
        
        Args:
            code_block: Code block to analyze
            
        Returns:
            Detected language string
        """
        code_lower = code_block.lower()
        
        # Common language patterns
        if 'def ' in code_lower or 'import ' in code_lower or 'class ' in code_lower:
            return 'python'
        elif 'function' in code_lower or 'const ' in code_lower or 'let ' in code_lower:
            return 'javascript'
        elif 'public class' in code_lower or 'private ' in code_lower:
            return 'java'
        elif '#include' in code_lower or 'int main' in code_lower:
            return 'cpp'
        elif 'fn ' in code_lower or 'let mut' in code_lower:
            return 'rust'
        elif 'func ' in code_lower or 'package ' in code_lower:
            return 'go'
        elif '<html' in code_lower or '<div' in code_lower:
            return 'html'
        elif 'SELECT' in code_block.upper() or 'FROM' in code_block.upper():
            return 'sql'
        else:
            return ''  # No language detection

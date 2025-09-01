"""Markdown formatter for CodeRabbit comment output."""

import re
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

    def format(self, persona: str, analyzed_comments: AnalyzedComments, quiet: bool = False) -> str:
        """Format analyzed comments as Markdown.

        Args:
            persona: AI persona prompt string
            analyzed_comments: Analyzed CodeRabbit comments
            quiet: Use quiet mode for minimal AI-optimized output

        Returns:
            Formatted Markdown string
        """
        # If in quiet mode, use AI-optimized simplified format
        if quiet:
            return self._format_quiet_mode(analyzed_comments)
            
        sections = []

        # Title and Persona
        sections.append("# CodeRabbit Analysis Report")
        sections.append("")
        
        # Include persona only if not in quiet mode
        if self.include_metadata:
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
            priority = self._extract_priority_level(comment.issue_description or "")
            priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")

            sections.append(f"{i}. {priority_icon} **{comment.title}**")

            if comment.issue_description:
                sections.append(f"   {comment.issue_description}")

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

            if comment.issue_description:
                sections.append(f"   {comment.issue_description}")

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
            content = " ".join([c.issue_description or "" for c in review.actionable_comments])
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
    
    def _format_quiet_mode(self, analyzed_comments: AnalyzedComments) -> str:
        """Format analyzed comments in quiet mode with AI-agent optimized structure.
        
        Args:
            analyzed_comments: Analyzed CodeRabbit comments
            
        Returns:
            Structured Markdown string optimized for AI processing
        """
        sections = []
        
        # Collect and organize all actionable items by priority and file
        items_by_priority = {'high': [], 'medium': [], 'low': []}
        items_by_file = {}
        all_items = []
        
        # Extract from review comments
        if analyzed_comments.review_comments:
            for review in analyzed_comments.review_comments:
                if review.actionable_comments:
                    for comment in review.actionable_comments:
                        item = self._create_structured_item(comment)
                        if item:
                            all_items.append(item)
                            # Group by priority
                            items_by_priority[item['priority']].append(item)
                            # Group by file
                            if item['file']:
                                if item['file'] not in items_by_file:
                                    items_by_file[item['file']] = []
                                items_by_file[item['file']].append(item)
        
        # Extract from thread contexts (important for inline comments)
        if analyzed_comments.unresolved_threads:
            for thread in analyzed_comments.unresolved_threads:
                # Extract actionable items from thread contextual summary
                if hasattr(thread, 'contextual_summary') and thread.contextual_summary:
                    actionable_items = self._extract_actionable_from_thread(thread)
                    for item in actionable_items:
                        if item:
                            all_items.append(item)
                            # Group by priority
                            items_by_priority[item['priority']].append(item)
                            # Group by file
                            if item['file']:
                                if item['file'] not in items_by_file:
                                    items_by_file[item['file']] = []
                                items_by_file[item['file']].append(item)
        
        # Remove duplicates based on content and location
        unique_items = self._deduplicate_items(all_items)
        
        if not unique_items:
            return "# No actionable CodeRabbit issues found"
        
        # Build structured output
        sections.append("# CodeRabbit Analysis Summary")
        sections.append("")
        
        # Overview section
        high_count = len([i for i in unique_items if i['priority'] == 'high'])
        medium_count = len([i for i in unique_items if i['priority'] == 'medium'])
        low_count = len([i for i in unique_items if i['priority'] == 'low'])
        
        sections.append("## Overview")
        sections.append(f"- **Total Issues**: {len(unique_items)}")
        sections.append(f"- **Priority Breakdown**: {high_count} Critical, {medium_count} Important, {low_count} Minor")
        sections.append(f"- **Files Affected**: {len(items_by_file)}")
        sections.append("")
        
        # Priority-based sections
        if high_count > 0:
            sections.append("## 🔴 Critical Issues (Immediate Action Required)")
            for item in [i for i in unique_items if i['priority'] == 'high']:
                sections.append(f"• **{item['category']}**: {item['title']}")
                line_suffix = f":{item['line']}" if item['line'] else ""
                sections.append(f"  - File: `{item['file']}{line_suffix}`")
                sections.append(f"  - Action: {item['action']}")
                sections.append("")
        
        if medium_count > 0:
            sections.append("## 🟡 Important Issues (Should Fix Soon)")
            for item in [i for i in unique_items if i['priority'] == 'medium']:
                sections.append(f"• **{item['category']}**: {item['title']}")
                line_suffix = f":{item['line']}" if item['line'] else ""
                sections.append(f"  - File: `{item['file']}{line_suffix}`")
                sections.append("")
        
        if low_count > 0:
            sections.append("## 🟢 Minor Issues (Optional Improvements)")
            for item in [i for i in unique_items if i['priority'] == 'low']:
                line_suffix = f":{item['line']}" if item['line'] else ""
                sections.append(f"• {item['title']} (`{item['file']}{line_suffix}`)")
        
        # File-based summary
        if len(items_by_file) > 0:
            sections.append("")
            sections.append("## Files Summary")
            for file_path, file_items in sorted(items_by_file.items()):
                sections.append(f"- **{file_path}**: {len(file_items)} issue(s)")
        
        return "\n".join(sections)

    def _extract_actionable_from_thread(self, thread) -> List[dict]:
        """Extract actionable items from a thread context.
        
        Args:
            thread: ThreadContext object
            
        Returns:
            List of structured item dictionaries
        """
        items = []
        
        # Get thread content - prioritize contextual_summary
        content = getattr(thread, 'contextual_summary', '') or ''
        if hasattr(thread, 'ai_summary') and thread.ai_summary:
            content += ' ' + thread.ai_summary
        
        if not content:
            return items
        
        # Extract file context
        file_context = getattr(thread, 'file_context', '') or ''
        line_context = getattr(thread, 'line_context', '') or ''
        
        # Look for actionable indicators in the content
        actionable_indicators = [
            r'副作用が大きいです.*修正してください',
            r'壊さないよう.*修正',
            r'安全です',
            r'問題.*修正',
            r'エラー.*修正',
            r'バグ.*修正',
            r'脆弱性.*対策',
            r'セキュリティ.*修正'
        ]
        
        for pattern in actionable_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                # Determine priority based on content
                priority = 'high'
                if any(keyword in content.lower() for keyword in ['critical', '危険', 'security', 'vulnerability']):
                    priority = 'high'
                elif any(keyword in content.lower() for keyword in ['副作用', '壊す', '修正']):
                    priority = 'medium'
                else:
                    priority = 'low'
                
                # Create structured item
                item = {
                    'title': self._extract_main_issue_from_content(content),
                    'file': self._clean_file_path(file_context),
                    'line': self._extract_line_from_context(line_context),
                    'priority': priority,
                    'category': self._categorize_thread_content(content),
                    'action': self._extract_action_from_content(content),
                    'raw': content
                }
                
                if item['file'] and item['title']:
                    items.append(item)
                break  # Avoid duplicates from same thread
        
        return items
    
    def _extract_main_issue_from_content(self, content: str) -> str:
        """Extract the main issue description from thread content.
        
        Args:
            content: Thread content text
            
        Returns:
            Main issue description
        """
        # Look for key phrases that describe the issue
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and any(indicator in line for indicator in ['副作用', '修正', '問題', 'エラー', 'バグ']):
                # Clean up the line
                cleaned = re.sub(r'^[*\-•]\s*', '', line)  # Remove bullet points
                cleaned = re.sub(r'^\*\*|\*\*$', '', cleaned)  # Remove bold markers
                cleaned = cleaned.strip()
                if len(cleaned) > 20:  # Only return substantial descriptions
                    return cleaned[:100]  # Truncate if too long
        
        # Fallback: return first non-empty line
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                return line[:100]
        
        return content[:100] if content else "Issue description not available"
    
    def _categorize_thread_content(self, content: str) -> str:
        """Categorize thread content to determine issue category.
        
        Args:
            content: Thread content text
            
        Returns:
            Category string
        """
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['security', 'vulnerability', 'セキュリティ', '脆弱性']):
            return 'Security'
        elif any(keyword in content_lower for keyword in ['configuration', 'config', '設定', 'キーボード']):
            return 'Configuration'
        elif any(keyword in content_lower for keyword in ['error', 'exception', 'エラー', '例外']):
            return 'Error Handling'
        elif any(keyword in content_lower for keyword in ['performance', 'パフォーマンス', '性能']):
            return 'Performance'
        elif any(keyword in content_lower for keyword in ['bug', 'バグ', '不具合']):
            return 'Bug Fix'
        elif any(keyword in content_lower for keyword in ['documentation', 'doc', 'ドキュメント']):
            return 'Documentation'
        else:
            return 'General'
    
    def _extract_action_from_content(self, content: str) -> str:
        """Extract suggested action from thread content.
        
        Args:
            content: Thread content text
            
        Returns:
            Action description
        """
        if '修正してください' in content:
            return 'Modify implementation to avoid side effects'
        elif '安全です' in content:
            return 'Use safer alternative approach'
        elif 'リセット' in content:
            return 'Reset options only instead of changing layout'
        else:
            return 'Review and address the identified issue'
    
    def _extract_line_from_context(self, line_context: str) -> str:
        """Extract line number from line context.
        
        Args:
            line_context: Line context string
            
        Returns:
            Line number as string
        """
        if not line_context:
            return ""
        
        # Extract number from line context
        match = re.search(r'\d+', line_context)
        return match.group(0) if match else ""
    
    def _create_structured_item(self, comment) -> dict:
        """Create a structured item from an actionable comment.
        
        Args:
            comment: ActionableComment object
            
        Returns:
            Dictionary with structured item data
        """
        # Clean file path
        clean_file = self._clean_file_path(getattr(comment, 'file_path', ''))
        if not clean_file:
            return None
        
        # Get line number with improved extraction
        line_num = self._extract_line_number(comment)
        
        # Clean and process title/description
        title = self._clean_title(getattr(comment, 'title', '') or getattr(comment, 'issue_description', ''))
        
        # Determine category and action
        category, action = self._categorize_comment(comment)
        
        return {
            'title': title,
            'file': clean_file,
            'line': line_num,
            'priority': getattr(comment, 'priority', 'medium').lower(),
            'category': category,
            'action': action,
            'raw': getattr(comment, 'raw_content', '')
        }
    
    def _clean_file_path(self, file_path: str) -> str:
        """Clean and normalize file path with improved accuracy.
        
        Args:
            file_path: Raw file path from CodeRabbit comment
            
        Returns:
            Cleaned file path or empty string if invalid
        """
        if not file_path or file_path in ['--', '-', '', 'None', 'null', 'N/A', 'undefined']:
            return ''
        
        # Convert to string and clean basic formatting
        clean_path = str(file_path).strip().strip('"').strip("'").strip('`')
        
        # Skip clearly invalid patterns - enhanced for current issues
        invalid_patterns = [
            r'^\s*[-*+]\s*', # Bullet points
            r'^\s*Type=', # Desktop file metadata
            r'^\s*TryExec=', # Desktop file metadata
            r'^\s*\+[A-Z_]+=', # Environment variable assignments
            r'metadata\s*$', # Lines ending with metadata
            r';\s*\\$', # Lines ending with backslash
            r'^\s*[^/]*\s+\(1\s+hunks?\)', # "filename (1 hunk)"
            r'^\s*[^/]*の\d+行目', # Japanese line references
            r'^\s*(http|https|ftp)://', # URLs
            r'^\s*(Comment|comment|Review|review)', # Comment indicators
            r'^\s*Line\s+\d+', # Line references
            r'^\s*Lines\s+\d+', # Line references
            r'^\s*##?\s*', # Markdown headers
            r'^\s*\*\*.*\*\*\s*$', # Bold text only
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, clean_path):
                return ''
        
        # Remove markdown formatting artifacts
        clean_path = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_path)  # Remove bold
        clean_path = clean_path.replace('**', '').replace('*', '').replace('`', '')
        
        # Handle bracketed content like [filename.py]
        if clean_path.startswith('[') and clean_path.endswith(']'):
            clean_path = clean_path[1:-1]
        
        # Remove line number suffixes like "filename.py:123" or "filename.py (line 123)"
        if ':' in clean_path:
            parts = clean_path.split(':')
            # Keep the main path, ignore line numbers
            clean_path = parts[0].strip()
        
        if '(' in clean_path and ('line' in clean_path.lower() or 'hunk' in clean_path.lower()):
            clean_path = clean_path.split('(')[0].strip()
        
        # Validate that it looks like a file path
        if not clean_path or len(clean_path) < 2:
            return ''
            
        # Must contain at least one letter and have reasonable length
        if not any(c.isalpha() for c in clean_path) or len(clean_path) > 200:
            return ''
        
        # Check for valid file extension patterns
        valid_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.c', '.cpp',
            '.h', '.hpp', '.cs', '.php', '.rb', '.swift', '.kt', '.scala', '.sh',
            '.md', '.txt', '.yaml', '.yml', '.json', '.xml', '.html', '.css',
            '.sql', '.dockerfile', '.makefile', '.toml', '.ini', '.desktop', '.conf'
        ]
        
        has_extension = any(clean_path.lower().endswith(ext) for ext in valid_extensions)
        
        # If it's a relative or absolute path, preserve the structure
        if '/' in clean_path:
            # For paths like "src/components/Button.tsx", keep the full path for context
            if has_extension and len(clean_path.split('/')) <= 4:  # Not too deep
                return clean_path
            elif has_extension:
                # For very deep paths, show last 2 directories
                parts = clean_path.split('/')
                if len(parts) > 3:
                    return f".../{'/'.join(parts[-2:])}"
                return clean_path
            else:
                # No extension but has path - try to extract filename
                filename = clean_path.split('/')[-1]
                if filename and len(filename) > 1 and any(c.isalpha() for c in filename):
                    return clean_path  # Keep full path even without extension
                return ''
        
        # Single filename
        if has_extension:
            return clean_path
        elif '.' in clean_path and len(clean_path.split('.')[-1]) <= 5:  # Reasonable extension length
            return clean_path
        elif clean_path.lower() in ['makefile', 'dockerfile', 'rakefile', 'cmake']:  # Common files without extensions
            return clean_path
        elif re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', clean_path):  # Simple valid filename
            return clean_path
        
        return ''
    
    def _extract_line_number(self, comment) -> str:
        """Extract line number from comment with improved accuracy.
        
        Args:
            comment: ActionableComment object
            
        Returns:
            Line number as string or empty string if not found
        """
        # Try direct line_number attribute first
        line_num = getattr(comment, 'line_number', None)
        if line_num:
            # Clean and validate line number
            try:
                line_str = str(line_num).strip()
                if line_str.isdigit() and int(line_str) > 0:
                    return line_str
            except (ValueError, TypeError):
                pass
        
        # Try line_range attribute
        line_range = getattr(comment, 'line_range', None)
        if line_range:
            line_range_str = str(line_range).strip()
            
            # Handle ranges like "123-125" or "123..125"
            if '-' in line_range_str:
                start_line = line_range_str.split('-')[0].strip()
                try:
                    if start_line.isdigit() and int(start_line) > 0:
                        return start_line
                except (ValueError, TypeError):
                    pass
            elif '..' in line_range_str:
                start_line = line_range_str.split('..')[0].strip()
                try:
                    if start_line.isdigit() and int(start_line) > 0:
                        return start_line
                except (ValueError, TypeError):
                    pass
            else:
                # Single line number
                try:
                    if line_range_str.isdigit() and int(line_range_str) > 0:
                        return line_range_str
                except (ValueError, TypeError):
                    pass
        
        # Try extracting from raw content or other fields
        raw_content = getattr(comment, 'raw_content', '')
        if raw_content:
            import re
            # Look for patterns like "Line 123:" or "at line 123"
            line_patterns = [
                r'[Ll]ine\s+(\d+)',
                r'at\s+line\s+(\d+)',
                r':\s*(\d+):\d+',  # file.py:123:45 format
                r'#L(\d+)',        # GitHub line anchor format
            ]
            
            for pattern in line_patterns:
                matches = re.findall(pattern, raw_content)
                if matches:
                    try:
                        line_num = int(matches[0])
                        if line_num > 0:
                            return str(line_num)
                    except (ValueError, IndexError):
                        continue
        
        return ''
    
    def _clean_title(self, title: str) -> str:
        """Clean and normalize title text with improved accuracy.
        
        Args:
            title: Raw title text
            
        Returns:
            Cleaned title
        """
        if not title:
            return "CodeRabbit suggestion"
        
        # Remove markdown formatting and extra characters
        clean_title = title.strip()
        
        # Remove markdown code blocks and formatting
        if clean_title.startswith('`') and clean_title.endswith('`'):
            clean_title = clean_title[1:-1]
        
        # Remove bold formatting
        clean_title = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_title)
        clean_title = clean_title.replace('**', '').replace('*', '')
        
        # Remove leading numbers, bullet points, and formatting
        clean_title = re.sub(r'^\d+\.\s*', '', clean_title)  # Remove "1. "
        clean_title = re.sub(r'^[-*+]\s*', '', clean_title)  # Remove bullet points
        clean_title = clean_title.strip()
        
        # Remove trailing code block markers
        clean_title = re.sub(r'\s*```\s*$', '', clean_title)
        clean_title = re.sub(r'\s*`\s*$', '', clean_title)
        
        # If the title looks like a file path or metadata, try to extract meaningful content
        if any(pattern in clean_title for pattern in ['=', '${', '}', 'Type=', 'TryExec=']):
            # For desktop file metadata, return a meaningful description
            if 'Type=' in clean_title:
                return 'Desktop file configuration'
            elif 'TryExec=' in clean_title:
                return 'Executable path configuration'
            elif '${' in clean_title and '}' in clean_title:
                return 'Environment variable usage'
            else:
                return 'Configuration issue'
        
        # If title is too short or just whitespace/symbols, provide fallback
        if len(clean_title.strip()) < 3 or not any(c.isalpha() for c in clean_title):
            return "Configuration issue"
        
        # Truncate if too long but preserve sentence structure
        if len(clean_title) > 100:
            # Try to break at sentence boundary
            sentences = clean_title.split('。')  # Japanese sentence ending
            if len(sentences) > 1 and len(sentences[0]) <= 100:
                clean_title = sentences[0] + '。'
            else:
                # Break at reasonable word boundary
                words = clean_title[:97].split()
                if len(words) > 1:
                    clean_title = ' '.join(words[:-1]) + "..."
                else:
                    clean_title = clean_title[:97] + "..."
        
        return clean_title or "CodeRabbit suggestion"
    
    def _categorize_comment(self, comment) -> tuple:
        """Categorize comment and provide specific actionable guidance.
        
        Args:
            comment: ActionableComment object
            
        Returns:
            Tuple of (category, specific_action_guidance)
        """
        content = (getattr(comment, 'issue_description', '') + ' ' + 
                  getattr(comment, 'raw_content', '')).lower()
        title = getattr(comment, 'title', '').lower()
        
        # Security issues - specific actions
        if any(word in content for word in ['security', 'vulnerability', 'csrf', 'xss', 'sql injection']):
            if 'auth' in content or 'token' in content:
                return 'Security', 'Review authentication/token handling - validate input, use secure storage'
            elif 'password' in content or 'credential' in content:
                return 'Security', 'Secure credential handling - hash passwords, use environment variables'
            elif 'input' in content or 'sanitiz' in content:
                return 'Security', 'Sanitize user input - validate, escape, and filter all inputs'
            else:
                return 'Security', 'Address security vulnerability - review code for potential exploits'
        
        # Performance issues - specific optimizations
        if any(word in content for word in ['performance', 'slow', 'optimize', 'efficiency', 'memory', 'cpu']):
            if 'loop' in content or 'iteration' in content:
                return 'Performance', 'Optimize loop performance - consider caching, break conditions, or vectorization'
            elif 'query' in content or 'database' in content or 'db' in content:
                return 'Performance', 'Optimize database queries - add indexes, use pagination, avoid N+1 queries'
            elif 'memory' in content:
                return 'Performance', 'Reduce memory usage - use generators, release references, optimize data structures'
            elif 'cache' in content:
                return 'Performance', 'Implement caching strategy - add memoization, Redis cache, or HTTP cache headers'
            else:
                return 'Performance', 'Improve performance - profile code, identify bottlenecks, optimize algorithms'
        
        # Error handling - specific improvements
        if any(word in content for word in ['error', 'exception', 'handle', 'catch', 'try', 'fail']):
            if 'logging' in content or 'log' in content:
                return 'Error Handling', 'Improve error logging - add structured logging, include context, set appropriate levels'
            elif 'validation' in content or 'validate' in content:
                return 'Error Handling', 'Add input validation - check types, ranges, required fields before processing'
            elif 'recovery' in content or 'fallback' in content:
                return 'Error Handling', 'Implement error recovery - add fallback mechanisms, retry logic, graceful degradation'
            else:
                return 'Error Handling', 'Enhance error handling - add try-catch blocks, proper error messages, user feedback'
        
        # Documentation issues - specific actions
        if any(word in content for word in ['document', 'comment', 'readme', 'doc', 'explain']):
            if 'api' in content:
                return 'Documentation', 'Document API - add endpoint descriptions, parameter details, response examples'
            elif 'function' in content or 'method' in content:
                return 'Documentation', 'Add function documentation - include purpose, parameters, return values, examples'
            elif 'readme' in content:
                return 'Documentation', 'Update README - add installation steps, usage examples, configuration details'
            else:
                return 'Documentation', 'Improve documentation - add inline comments, usage examples, clear explanations'
        
        # Code style/quality - specific fixes
        if any(word in content for word in ['style', 'format', 'lint', 'naming', 'convention']):
            if 'naming' in content or 'name' in content:
                return 'Code Style', 'Improve naming - use descriptive variable/function names, follow conventions'
            elif 'format' in content or 'indent' in content:
                return 'Code Style', 'Fix formatting - run code formatter, ensure consistent indentation and spacing'
            elif 'complexity' in content or 'complex' in content:
                return 'Code Style', 'Reduce complexity - extract functions, simplify conditions, improve readability'
            else:
                return 'Code Style', 'Follow coding standards - apply style guide, fix linting issues, improve consistency'
        
        # Testing issues
        if any(word in content for word in ['test', 'testing', 'coverage', 'mock', 'unit test']):
            if 'coverage' in content:
                return 'Testing', 'Increase test coverage - add unit tests for uncovered code paths'
            elif 'mock' in content:
                return 'Testing', 'Improve test mocking - isolate dependencies, use proper test doubles'
            else:
                return 'Testing', 'Add comprehensive tests - include unit tests, edge cases, error scenarios'
        
        # Type safety
        if any(word in content for word in ['type', 'typing', 'annotation', 'interface', 'generic']):
            return 'Type Safety', 'Improve type annotations - add type hints, define interfaces, handle optional types'
        
        # Configuration/Environment
        if any(word in content for word in ['config', 'environment', 'env', 'settings']):
            return 'Configuration', 'Improve configuration - use environment variables, validate settings, add defaults'
        
        # API/Integration
        if any(word in content for word in ['api', 'endpoint', 'http', 'request', 'response']):
            return 'API Design', 'Improve API design - validate inputs, handle errors, document endpoints, use proper status codes'
        
        # Data handling
        if any(word in content for word in ['data', 'json', 'xml', 'parse', 'serialize']):
            return 'Data Handling', 'Improve data processing - validate structure, handle parsing errors, sanitize outputs'
        
        # Concurrency/Threading
        if any(word in content for word in ['thread', 'async', 'concurrent', 'race', 'deadlock']):
            return 'Concurrency', 'Fix concurrency issues - add proper synchronization, avoid race conditions, handle async operations'
        
        # Default with content analysis
        if 'should' in content or 'consider' in content:
            return 'Suggestion', 'Review suggestion - evaluate recommendation and implement if beneficial'
        elif 'fix' in content or 'correct' in content:
            return 'Bug Fix', 'Address reported issue - debug problem, implement fix, add test to prevent regression'
        elif 'refactor' in content:
            return 'Refactoring', 'Refactor code - improve structure while maintaining functionality, enhance maintainability'
        
        # Fallback with basic categorization
        return 'General', 'Review and address the CodeRabbit suggestion - analyze recommendation and implement appropriate changes'
    
    def _deduplicate_items(self, items: list) -> list:
        """Remove duplicate items based on advanced content similarity detection.
        
        Args:
            items: List of structured items
            
        Returns:
            Deduplicated list with noise removed
        """
        if not items:
            return []
        
        # First pass: Remove clearly invalid items
        valid_items = []
        for item in items:
            if self._is_valid_item(item):
                valid_items.append(item)
        
        if not valid_items:
            return []
        
        # Second pass: Advanced deduplication
        unique_items = []
        processed_keys = set()
        
        for item in valid_items:
            # Create multiple similarity keys
            exact_key = f"{item['file']}:{item['line']}:{item['title']}"
            location_key = f"{item['file']}:{item['line']}"
            content_key = self._create_content_fingerprint(item['title'])
            
            # Check for exact duplicates
            if exact_key in processed_keys:
                continue
            
            # Check for same-location similar content
            is_duplicate = False
            for existing in unique_items:
                existing_location_key = f"{existing['file']}:{existing['line']}"
                existing_content_key = self._create_content_fingerprint(existing['title'])
                
                # Same location check
                if location_key == existing_location_key:
                    # If same location, merge or skip based on priority/quality
                    if self._should_merge_items(item, existing):
                        # Replace with higher quality item
                        unique_items.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
                
                # Similar content check (different locations)
                elif self._are_contents_similar(content_key, existing_content_key):
                    # Keep the one with better location info or higher priority
                    if self._is_better_item(item, existing):
                        unique_items.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_items.append(item)
                processed_keys.add(exact_key)
        
        # Third pass: Quality-based filtering
        return self._filter_by_quality(unique_items)
    
    def _is_valid_item(self, item: dict) -> bool:
        """Check if an item is valid and should be included.
        
        Args:
            item: Structured item dictionary
            
        Returns:
            True if item is valid
        """
        # Must have a clean file path
        file_path = item.get('file', '').strip()
        if not file_path or len(file_path) < 2:
            return False
        
        # Skip file paths that are clearly metadata or invalid
        invalid_file_patterns = [
            r'^[^/]*\s+(1\s+hunks?)', # "filename (1 hunk)"
            r'^\s*[+\-*]\s*["\']', # Lines starting with symbols and quotes
            r'^\s*Type=', # Desktop file metadata
            r'^\s*TryExec=', # Desktop file metadata
            r'^\s*\+[A-Z_]+=', # Environment variable assignments
            r'metadata$', # Files ending with metadata
            r';\s*\\$', # Lines ending with backslash
            r'^\s*[^/]*の\d+行目', # Japanese line references
            r'^\s*\w+\s*$', # Single words that are likely categories
        ]
        
        for pattern in invalid_file_patterns:
            if re.match(pattern, file_path):
                return False
        
        # Must have meaningful title
        title = item.get('title', '').strip()
        if not title or len(title) < 5:
            return False
        
        # Skip noise titles
        noise_patterns = [
            r'^[+\-*]\s*',  # Bullet points
            r'^\d+\.\s*$',  # Just numbers
            r'^[^a-zA-Z]*$', # No alphabetic characters
            r'^(coderabbit|review|comment|suggestion|nitpick|fix|update|change)\s*$', # Generic terms
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, title.lower()):
                return False
        
        return True
    
    def _create_content_fingerprint(self, content: str) -> str:
        """Create a content fingerprint for similarity detection.
        
        Args:
            content: Content string
            
        Returns:
            Normalized fingerprint string
        """
        if not content:
            return ''
        
        # Normalize text
        normalized = content.lower().strip()
        
        # Remove common formatting and noise words
        noise_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = normalized.split()
        
        # Filter out noise words and short words
        significant_words = [w for w in words if len(w) > 2 and w not in noise_words]
        
        # Create fingerprint from first few significant words
        fingerprint_words = significant_words[:5]  # Use first 5 significant words
        return ' '.join(sorted(fingerprint_words))  # Sort for consistency
    
    def _are_contents_similar(self, content1: str, content2: str) -> bool:
        """Check if two content fingerprints are similar.
        
        Args:
            content1: First content fingerprint
            content2: Second content fingerprint
            
        Returns:
            True if contents are similar
        """
        if not content1 or not content2:
            return False
        
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return False
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = intersection / union if union > 0 else 0
        
        # Consider similar if > 60% overlap
        return similarity > 0.6
    
    def _should_merge_items(self, item1: dict, item2: dict) -> bool:
        """Check if item1 should replace item2 (same location).
        
        Args:
            item1: New item
            item2: Existing item
            
        Returns:
            True if item1 should replace item2
        """
        # Prefer items with higher priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        
        item1_priority = priority_order.get(item1.get('priority', 'medium'), 2)
        item2_priority = priority_order.get(item2.get('priority', 'medium'), 2)
        
        if item1_priority != item2_priority:
            return item1_priority > item2_priority
        
        # Prefer items with more detailed titles
        item1_length = len(item1.get('title', ''))
        item2_length = len(item2.get('title', ''))
        
        if abs(item1_length - item2_length) > 10:  # Significant difference
            return item1_length > item2_length
        
        # Prefer items with specific actions
        if item1.get('category') != item2.get('category'):
            specific_categories = ['Security', 'Performance', 'Error Handling']
            item1_specific = item1.get('category') in specific_categories
            item2_specific = item2.get('category') in specific_categories
            
            return item1_specific and not item2_specific
        
        return False
    
    def _is_better_item(self, item1: dict, item2: dict) -> bool:
        """Check if item1 is better than item2 (different locations).
        
        Args:
            item1: New item
            item2: Existing item
            
        Returns:
            True if item1 is better
        """
        # Prefer items with line numbers
        item1_has_line = bool(item1.get('line'))
        item2_has_line = bool(item2.get('line'))
        
        if item1_has_line != item2_has_line:
            return item1_has_line
        
        # Then apply merge criteria
        return self._should_merge_items(item1, item2)
    
    def _filter_by_quality(self, items: list) -> list:
        """Final quality-based filtering.
        
        Args:
            items: List of deduplicated items
            
        Returns:
            Quality-filtered list
        """
        if len(items) <= 10:  # If we have few items, keep all
            return items
        
        # If too many items, prioritize by importance
        high_priority = [item for item in items if item.get('priority') == 'high']
        medium_priority = [item for item in items if item.get('priority') == 'medium']
        low_priority = [item for item in items if item.get('priority') == 'low']
        
        # Keep all high priority, limit medium and low
        result = high_priority
        result.extend(medium_priority[:8])  # Max 8 medium priority
        result.extend(low_priority[:4])     # Max 4 low priority
        
        return result

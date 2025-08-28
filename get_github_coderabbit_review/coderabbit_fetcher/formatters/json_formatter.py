"""JSON formatter for CodeRabbit comment output."""

import json
from typing import Dict, Any, List, Optional
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


class JSONFormatter(BaseFormatter):
    """JSON formatter for structured CodeRabbit comment output."""

    def __init__(self, pretty_print: bool = True, include_raw_content: bool = False):
        """Initialize JSON formatter.

        Args:
            pretty_print: Whether to format JSON with indentation
            include_raw_content: Whether to include raw comment content
        """
        super().__init__()
        self.pretty_print = pretty_print
        self.include_raw_content = include_raw_content

    def format(self, persona: str, analyzed_comments: AnalyzedComments) -> str:
        """Format analyzed comments as JSON.

        Args:
            persona: AI persona prompt string
            analyzed_comments: Analyzed CodeRabbit comments

        Returns:
            Formatted JSON string
        """
        output = {
            "metadata": self._format_metadata(analyzed_comments),
            "persona": persona,
            "summary_comments": self._format_summary_comments(analyzed_comments.summary_comments),
            "review_comments": self._format_review_comments(analyzed_comments.review_comments),
            "thread_contexts": self._format_thread_contexts(analyzed_comments.unresolved_threads)
        }

        if self.pretty_print:
            return json.dumps(output, indent=2, ensure_ascii=False, default=self._json_serializer)
        else:
            return json.dumps(output, ensure_ascii=False, default=self._json_serializer)

    def format_ai_agent_prompt(self, prompt: AIAgentPrompt) -> Dict[str, Any]:
        """Format AI agent prompt as JSON structure.

        Args:
            prompt: AI agent prompt to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "type": "ai_agent_prompt",
            "description": prompt.description,
            "file_path": prompt.file_path,
            "line_range": prompt.line_range,
            "code_block": prompt.code_block,
            "language": getattr(prompt, 'language', None),
            "is_complete_suggestion": getattr(prompt, 'is_complete_suggestion', False)
        }

    def format_thread_context(self, thread: ThreadContext) -> Dict[str, Any]:
        """Format thread context as JSON structure.

        Args:
            thread: Thread context to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "thread_id": getattr(thread, 'thread_id', None),
            "root_comment_id": getattr(thread, 'root_comment_id', None),
            "resolution_status": str(thread.resolution_status),
            "file_context": getattr(thread, 'file_context', None),
            "line_context": getattr(thread, 'line_context', None),
            "participants": getattr(thread, 'participants', []),
            "comment_count": getattr(thread, 'comment_count', len(thread.chronological_order) if thread.chronological_order else 0),
            "coderabbit_comment_count": getattr(thread, 'coderabbit_comment_count', 0),
            "is_resolved": getattr(thread, 'is_resolved', False),
            "context_summary": getattr(thread, 'context_summary', None),
            "ai_summary": getattr(thread, 'ai_summary', None),
            "contextual_summary": thread.contextual_summary,
            "chronological_comments": self._format_chronological_comments(thread.chronological_order)
        }

    def _format_metadata(self, analyzed_comments: AnalyzedComments) -> Dict[str, Any]:
        """Format metadata section.

        Args:
            analyzed_comments: Analyzed comments for metadata

        Returns:
            Metadata dictionary
        """
        metadata = self.format_metadata(analyzed_comments)

        return {
            "generated_at": metadata["timestamp"],
            "formatter_type": metadata["formatter_type"],
            "statistics": {
                "total_comments": metadata["total_comments"],
                "summary_count": metadata["summary_count"],
                "review_count": metadata["review_count"],
                "thread_count": metadata["total_threads"]
            },
            "configuration": {
                "pretty_print": self.pretty_print,
                "include_raw_content": self.include_raw_content
            }
        }

    def _format_summary_comments(self, summary_comments: Optional[List[SummaryComment]]) -> List[Dict[str, Any]]:
        """Format summary comments as JSON structures.

        Args:
            summary_comments: List of summary comments

        Returns:
            List of JSON-serializable dictionaries
        """
        if not summary_comments:
            return []

        formatted = []
        for summary in summary_comments:
            summary_dict = {
                "walkthrough": summary.walkthrough,
                "new_features": summary.new_features,
                "documentation_changes": summary.documentation_changes,
                "test_changes": summary.test_changes,
                "changes_table": [{"cohort_or_files": c.cohort_or_files, "summary": c.summary} for c in summary.changes_table],
                "sequence_diagram": summary.sequence_diagram
            }

            # Add statistics
            summary_dict["statistics"] = {
                "total_changes": summary.total_changes,
                "has_new_features": summary.has_new_features,
                "has_documentation_changes": summary.has_documentation_changes,
                "has_test_changes": summary.has_test_changes,
                "has_sequence_diagram": summary.has_sequence_diagram
            }

            if self.include_raw_content:
                summary_dict["raw_content"] = summary.raw_content

            formatted.append(summary_dict)

        return formatted

    def _format_review_comments(self, review_comments: Optional[List[ReviewComment]]) -> List[Dict[str, Any]]:
        """Format review comments as JSON structures.

        Args:
            review_comments: List of review comments

        Returns:
            List of JSON-serializable dictionaries
        """
        if not review_comments:
            return []

        formatted = []
        for review in review_comments:
            review_dict = {
                "actionable_comments": [self._format_actionable_comment(c) for c in review.actionable_comments],
                "nitpick_comments": [self._format_nitpick_comment(c) for c in review.nitpick_comments],
                "outside_diff_comments": [self._format_outside_diff_comment(c) for c in review.outside_diff_comments],
                "ai_agent_prompts": [self.format_ai_agent_prompt(p) for p in review.ai_agent_prompts],
                "has_ai_prompts": getattr(review, 'has_ai_prompts', len(review.ai_agent_prompts) > 0)
            }

            if self.include_raw_content:
                review_dict["raw_content"] = review.raw_content

            # Add metadata
            review_dict["metadata"] = {
                "comment_type": self._determine_primary_type(review),
                "priority_level": self._extract_priority_from_review(review),
                "actionable_count": len(review.actionable_comments),
                "nitpick_count": len(review.nitpick_comments),
                "outside_diff_count": len(review.outside_diff_comments),
                "ai_prompt_count": len(review.ai_agent_prompts)
            }

            formatted.append(review_dict)

        return formatted

    def _format_thread_contexts(self, thread_contexts: Optional[List[ThreadContext]]) -> List[Dict[str, Any]]:
        """Format thread contexts as JSON structures.

        Args:
            thread_contexts: List of thread contexts

        Returns:
            List of JSON-serializable dictionaries
        """
        if not thread_contexts:
            return []

        return [self.format_thread_context(thread) for thread in thread_contexts]

    def _format_actionable_comment(self, comment: ActionableComment) -> Dict[str, Any]:
        """Format actionable comment as JSON structure.

        Args:
            comment: Actionable comment to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "type": "actionable",
            "title": comment.title,
            "description": comment.description,
            "file_path": comment.file_path,
            "line_number": comment.line_number,
            "priority": self._extract_priority_level(comment.description or "")
        }

    def _format_nitpick_comment(self, comment: NitpickComment) -> Dict[str, Any]:
        """Format nitpick comment as JSON structure.

        Args:
            comment: Nitpick comment to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "type": "nitpick",
            "suggestion": comment.suggestion,
            "file_path": comment.file_path,
            "line_number": comment.line_number,
            "category": self._categorize_nitpick(comment.suggestion)
        }

    def _format_outside_diff_comment(self, comment: OutsideDiffComment) -> Dict[str, Any]:
        """Format outside diff comment as JSON structure.

        Args:
            comment: Outside diff comment to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "type": "outside_diff",
            "issue": comment.issue,
            "description": comment.description,
            "file_path": comment.file_path,
            "line_range": comment.line_range,
            "severity": self._assess_severity(comment.issue, comment.description)
        }

    def _format_chronological_comments(self, chronological_order: Optional[List]) -> List[Dict[str, Any]]:
        """Format chronological comments as JSON structures.

        Args:
            chronological_order: List of chronological comments

        Returns:
            List of JSON-serializable dictionaries
        """
        if not chronological_order:
            return []

        formatted = []
        for i, comment in enumerate(chronological_order):
            comment_dict = {
                "sequence": i + 1,
                "content": self._extract_comment_content(comment),
                "type": self._identify_comment_source(comment)
            }

            # Add timestamp if available
            if hasattr(comment, 'created_at'):
                comment_dict["timestamp"] = getattr(comment, 'created_at', None)

            # Add author if available
            if hasattr(comment, 'user'):
                comment_dict["author"] = getattr(comment, 'user', {}).get('login', 'Unknown')

            formatted.append(comment_dict)

        return formatted

    def _determine_primary_type(self, review: ReviewComment) -> str:
        """Determine the primary type of a review comment.

        Args:
            review: Review comment to analyze

        Returns:
            Primary comment type string
        """
        if review.ai_agent_prompts:
            return "ai_agent_prompt"
        elif review.actionable_comments:
            return "actionable"
        elif review.nitpick_comments:
            return "nitpick"
        elif review.outside_diff_comments:
            return "outside_diff"
        else:
            return "general"

    def _extract_priority_from_review(self, review: ReviewComment) -> str:
        """Extract overall priority from review comment.

        Args:
            review: Review comment to analyze

        Returns:
            Priority level string
        """
        # Check actionable comments for highest priority
        priorities = []

        for comment in review.actionable_comments:
            priority = self._extract_priority_level(comment.description or "")
            priorities.append(priority)

        # Return highest priority found
        if "High" in priorities:
            return "High"
        elif "Medium" in priorities:
            return "Medium"
        elif priorities:
            return "Low"
        else:
            return "None"

    def _categorize_nitpick(self, suggestion: str) -> str:
        """Categorize nitpick suggestion.

        Args:
            suggestion: Nitpick suggestion text

        Returns:
            Category string
        """
        suggestion_lower = suggestion.lower()

        if any(keyword in suggestion_lower for keyword in ['format', 'style', 'indent', 'spacing']):
            return "formatting"
        elif any(keyword in suggestion_lower for keyword in ['name', 'naming', 'rename']):
            return "naming"
        elif any(keyword in suggestion_lower for keyword in ['comment', 'document', 'doc']):
            return "documentation"
        elif any(keyword in suggestion_lower for keyword in ['import', 'unused', 'remove']):
            return "cleanup"
        else:
            return "general"

    def _assess_severity(self, issue: str, description: Optional[str] = None) -> str:
        """Assess severity of outside diff comment.

        Args:
            issue: Issue title
            description: Optional issue description

        Returns:
            Severity level string
        """
        content = f"{issue} {description or ''}".lower()

        if any(keyword in content for keyword in ['critical', 'security', 'vulnerability', 'error']):
            return "high"
        elif any(keyword in content for keyword in ['warning', 'important', 'should']):
            return "medium"
        else:
            return "low"

    def _extract_comment_content(self, comment) -> str:
        """Extract content from comment object.

        Args:
            comment: Comment object to extract content from

        Returns:
            Comment content string
        """
        if hasattr(comment, 'body'):
            return self._sanitize_content(comment.body)
        elif hasattr(comment, 'content'):
            return self._sanitize_content(comment.content)
        elif isinstance(comment, str):
            return self._sanitize_content(comment)
        else:
            return str(comment)

    def _identify_comment_source(self, comment) -> str:
        """Identify the source/type of a comment.

        Args:
            comment: Comment object to identify

        Returns:
            Comment source string
        """
        if hasattr(comment, 'user'):
            user_login = getattr(comment, 'user', {}).get('login', '').lower()
            if 'coderabbit' in user_login:
                return "coderabbit"
            else:
                return "human"
        else:
            return "unknown"

    def _json_serializer(self, obj) -> str:
        """Custom JSON serializer for datetime and other objects.

        Args:
            obj: Object to serialize

        Returns:
            Serialized string representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)

"""Output formatting utilities for processed comments."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Handles formatting of processed comments for various output types."""

    def __init__(self) -> None:
        """Initialize the output formatter."""
        self.priority_emojis = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

    def format_actionable_comments(self, comments: List[Any]) -> List[Dict[str, Any]]:
        """Format actionable comments for output.

        Args:
            comments: List of ActionableComment objects

        Returns:
            List of formatted comment dictionaries
        """
        formatted = []

        for comment in comments:
            formatted_comment = {
                "id": getattr(comment, "id", ""),
                "description": getattr(comment, "description", ""),
                "suggestion": getattr(comment, "suggestion", ""),
                "file_path": getattr(comment, "file_path", ""),
                "line_number": getattr(comment, "line_number", 0),
                "priority": getattr(comment, "priority", "MEDIUM"),
                "type": getattr(comment, "comment_type", "general"),
                "raw_content": getattr(comment, "raw_content", ""),
            }

            # Add priority emoji
            priority = formatted_comment["priority"]
            formatted_comment["priority_display"] = (
                f"{self.priority_emojis.get(priority, '⚪')} {priority}"
            )

            formatted.append(formatted_comment)

        return formatted

    def format_nitpick_comments(self, comments: List[Any]) -> List[Dict[str, Any]]:
        """Format nitpick comments for output.

        Args:
            comments: List of NitpickComment objects

        Returns:
            List of formatted comment dictionaries
        """
        formatted = []

        for comment in comments:
            formatted_comment = {
                "suggestion": getattr(comment, "suggestion", ""),
                "file_path": getattr(comment, "file_path", ""),
                "line_number": getattr(comment, "line_number", 0),
                "priority": "LOW",  # Nitpicks are always low priority
                "type": "nitpick",
                "raw_content": getattr(comment, "raw_content", ""),
            }

            formatted_comment["priority_display"] = f"{self.priority_emojis['LOW']} LOW"

            formatted.append(formatted_comment)

        return formatted

    def format_outside_diff_comments(self, comments: List[Any]) -> List[Dict[str, Any]]:
        """Format outside diff comments for output.

        Args:
            comments: List of OutsideDiffComment objects

        Returns:
            List of formatted comment dictionaries
        """
        formatted = []

        for comment in comments:
            formatted_comment = {
                "suggestion": getattr(comment, "suggestion", ""),
                "file_path": getattr(comment, "file_path", ""),
                "line_range": getattr(comment, "line_range", ""),
                "priority": "MEDIUM",  # Outside diff comments are usually medium priority
                "type": "outside_diff",
                "raw_content": getattr(comment, "raw_content", ""),
            }

            formatted_comment["priority_display"] = f"{self.priority_emojis['MEDIUM']} MEDIUM"

            formatted.append(formatted_comment)

        return formatted

    def format_ai_agent_prompts(self, prompts: List[Any]) -> List[Dict[str, Any]]:
        """Format AI agent prompts for output.

        Args:
            prompts: List of AIAgentPrompt objects

        Returns:
            List of formatted prompt dictionaries
        """
        formatted = []

        for prompt in prompts:
            formatted_prompt = {
                "prompt_text": getattr(prompt, "prompt_text", ""),
                "context": getattr(prompt, "context", ""),
                "priority": "HIGH",  # AI prompts are usually high priority
                "type": "ai_agent_prompt",
                "raw_content": getattr(prompt, "raw_content", ""),
            }

            formatted_prompt["priority_display"] = f"{self.priority_emojis['HIGH']} HIGH"

            formatted.append(formatted_prompt)

        return formatted

    def group_by_priority(self, comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group comments by priority level.

        Args:
            comments: List of formatted comment dictionaries

        Returns:
            Dictionary with priority levels as keys and comment lists as values
        """
        grouped: dict[str, list[Any]] = {"HIGH": [], "MEDIUM": [], "LOW": []}

        for comment in comments:
            priority = comment.get("priority", "MEDIUM")
            if priority in grouped:
                grouped[priority].append(comment)

        return grouped

    def group_by_file(self, comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group comments by file path.

        Args:
            comments: List of formatted comment dictionaries

        Returns:
            Dictionary with file paths as keys and comment lists as values
        """
        grouped: dict[str, list[Any]] = {}

        for comment in comments:
            file_path = comment.get("file_path", "unknown")
            if file_path not in grouped:
                grouped[file_path] = []
            grouped[file_path].append(comment)

        return grouped

    def group_by_type(self, comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group comments by type.

        Args:
            comments: List of formatted comment dictionaries

        Returns:
            Dictionary with comment types as keys and comment lists as values
        """
        grouped: dict[str, list[Any]] = {}

        for comment in comments:
            comment_type = comment.get("type", "general")
            if comment_type not in grouped:
                grouped[comment_type] = []
            grouped[comment_type].append(comment)

        return grouped

    def create_summary_statistics(self, all_comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary statistics for all comments.

        Args:
            all_comments: List of all formatted comments

        Returns:
            Dictionary with summary statistics
        """
        total_comments = len(all_comments)

        by_priority = self.group_by_priority(all_comments)
        by_type = self.group_by_type(all_comments)
        by_file = self.group_by_file(all_comments)

        return {
            "total_comments": total_comments,
            "by_priority": {
                "high": len(by_priority["HIGH"]),
                "medium": len(by_priority["MEDIUM"]),
                "low": len(by_priority["LOW"]),
            },
            "by_type": {type_name: len(comments) for type_name, comments in by_type.items()},
            "files_affected": len(by_file),
            "files_with_most_comments": self._get_top_files(by_file, 5),
        }

    def format_for_display(
        self, comments: List[Dict[str, Any]], format_type: str = "compact"
    ) -> str:
        """Format comments for display output.

        Args:
            comments: List of formatted comment dictionaries
            format_type: Type of display format ('compact', 'detailed', 'summary')

        Returns:
            Formatted string for display
        """
        if format_type == "summary":
            return self._format_summary_display(comments)
        elif format_type == "detailed":
            return self._format_detailed_display(comments)
        else:
            return self._format_compact_display(comments)

    def _format_compact_display(self, comments: List[Dict[str, Any]]) -> str:
        """Format comments in compact display format."""
        lines = []

        by_priority = self.group_by_priority(comments)

        for priority in ["HIGH", "MEDIUM", "LOW"]:
            priority_comments = by_priority[priority]
            if priority_comments:
                emoji = self.priority_emojis[priority]
                lines.append(f"\n{emoji} **{priority} Priority** ({len(priority_comments)} items)")

                for comment in priority_comments:
                    file_info = (
                        f"{comment['file_path']}:{comment.get('line_number', '')}"
                        if comment["file_path"]
                        else ""
                    )
                    description = comment.get("description", comment.get("suggestion", ""))[:100]
                    if len(description) > 97:
                        description = description[:97] + "..."

                    lines.append(f"  • {description}")
                    if file_info:
                        lines.append(f"    📁 {file_info}")

        return "\n".join(lines)

    def _format_detailed_display(self, comments: List[Dict[str, Any]]) -> str:
        """Format comments in detailed display format."""
        lines = []

        for i, comment in enumerate(comments, 1):
            priority = comment.get("priority", "MEDIUM")
            emoji = self.priority_emojis.get(priority, "⚪")

            lines.append(f"\n## {i}. {emoji} {comment.get('description', 'No description')}")

            if comment.get("file_path"):
                lines.append(f"**File**: `{comment['file_path']}`")

            if comment.get("line_number"):
                lines.append(f"**Line**: {comment['line_number']}")

            if comment.get("suggestion"):
                lines.append(f"**Suggestion**: {comment['suggestion']}")

            lines.append(f"**Type**: {comment.get('type', 'general')}")
            lines.append(f"**Priority**: {priority}")

        return "\n".join(lines)

    def _format_summary_display(self, comments: List[Dict[str, Any]]) -> str:
        """Format comments in summary display format."""
        stats = self.create_summary_statistics(comments)

        lines = [
            "# 📊 Comments Summary",
            f"**Total Comments**: {stats['total_comments']}",
            "",
            "## Priority Breakdown",
            f"🔴 High: {stats['by_priority']['high']}",
            f"🟡 Medium: {stats['by_priority']['medium']}",
            f"🟢 Low: {stats['by_priority']['low']}",
            "",
            f"**Files Affected**: {stats['files_affected']}",
        ]

        if stats["files_with_most_comments"]:
            lines.append("\n## Files with Most Comments")
            for file_path, count in stats["files_with_most_comments"]:
                lines.append(f"• `{file_path}`: {count} comments")

        return "\n".join(lines)

    def _get_top_files(self, by_file: Dict[str, List], limit: int = 5) -> List[tuple]:
        """Get top files by comment count."""
        file_counts = [(file_path, len(comments)) for file_path, comments in by_file.items()]
        file_counts.sort(key=lambda x: x[1], reverse=True)
        return file_counts[:limit]

"""Comment analyzer for filtering and processing CodeRabbit comments."""

import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..models import AnalyzedComments, SummaryComment, ReviewComment, ActionableComment, ThreadContext, CommentMetadata
from ..exceptions import CommentParsingError
from ..processors import SummaryProcessor


class CommentAnalyzer:
    """Analyzes and filters CodeRabbit comments from GitHub PR data."""

    def __init__(self, resolved_marker: str = "🔒 CODERABBIT_RESOLVED 🔒"):
        """Initialize the comment analyzer.

        Args:
            resolved_marker: Marker text indicating a resolved comment thread
        """
        self.resolved_marker = resolved_marker
        self.coderabbit_author = "coderabbitai[bot]"
        self.summary_processor = SummaryProcessor()

    def analyze_comments(self, comments_data: Dict[str, Any]) -> AnalyzedComments:
        """Analyze GitHub PR comments and extract CodeRabbit-specific information.

        Args:
            comments_data: Raw GitHub API response containing PR comments

        Returns:
            AnalyzedComments object with processed comment data

        Raises:
            CommentParsingError: If comment data cannot be parsed
        """
        try:
            # Extract different comment types from the data
            inline_comments = comments_data.get("inline_comments", [])
            review_comments = comments_data.get("review_comments", [])
            pr_comments = comments_data.get("pr_comments", [])

            # Filter CodeRabbit comments
            coderabbit_inline = self.filter_coderabbit_comments(inline_comments)
            coderabbit_reviews = self.filter_coderabbit_comments(review_comments)
            coderabbit_pr_comments = self.filter_coderabbit_comments(pr_comments)

            # Group into threads and analyze resolution status
            inline_threads = self._group_into_threads(coderabbit_inline)
            review_threads = self._group_into_threads(coderabbit_reviews)

            # Filter out resolved threads
            unresolved_inline = self._filter_unresolved_threads(inline_threads)
            unresolved_reviews = self._filter_unresolved_threads(review_threads)

            # Process different comment types
            summary_comments = self._extract_summary_comments(coderabbit_pr_comments)
            actionable_comments = self._extract_actionable_comments(
                unresolved_inline + unresolved_reviews
            )

            # Create metadata (will be properly initialized from CLI)
            total_coderabbit = len(coderabbit_inline) + len(coderabbit_reviews) + len(coderabbit_pr_comments)
            resolved = len(inline_threads) + len(review_threads) - len(unresolved_inline) - len(unresolved_reviews)

            metadata = CommentMetadata(
                pr_number=0,  # Will be set from CLI
                pr_title="",  # Will be set from CLI
                owner="",     # Will be set from CLI
                repo="",      # Will be set from CLI
                processed_at=datetime.now(),
                total_comments=total_coderabbit,
                coderabbit_comments=total_coderabbit,
                resolved_comments=resolved,
                actionable_comments=len(actionable_comments),
                processing_time_seconds=0.0  # Will be calculated in CLI
            )

            # Convert unresolved comments to ReviewComment objects
            review_comments = []
            for comment in unresolved_inline + unresolved_reviews:
                review_comment = ReviewComment(
                    actionable_count=1,  # Each unresolved comment is considered actionable
                    raw_content=comment.get("body", "")
                )
                review_comments.append(review_comment)

            return AnalyzedComments(
                summary_comments=summary_comments,
                review_comments=review_comments,
                metadata=metadata,
                # Note: actionable_comments will be added in a future enhancement
                # For now, they are included in review_comments
            )

        except Exception as e:
            raise CommentParsingError(f"Failed to analyze comments: {str(e)}") from e

    def filter_coderabbit_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter comments to include only those from CodeRabbit.

        Args:
            comments: List of comment dictionaries from GitHub API

        Returns:
            List of CodeRabbit comments only
        """
        return [
            comment for comment in comments
            if self._is_coderabbit_comment(comment)
        ]

    def is_resolved(self, comment_thread: List[Dict[str, Any]]) -> bool:
        """Check if a comment thread is marked as resolved.

        Args:
            comment_thread: List of comments in chronological order

        Returns:
            True if the thread is marked as resolved
        """
        if not comment_thread:
            return False

        # Sort comments by creation time to find the last one
        sorted_comments = sorted(
            comment_thread,
            key=lambda c: c.get("created_at", "")
        )

        # Check if the last CodeRabbit comment contains the resolved marker
        for comment in reversed(sorted_comments):
            if self._is_coderabbit_comment(comment):
                body = comment.get("body", "")
                if self.resolved_marker in body:
                    return True
                # If we find a CodeRabbit comment without the marker, it's not resolved
                break

        return False

    def _is_coderabbit_comment(self, comment: Dict[str, Any]) -> bool:
        """Check if a comment is from CodeRabbit.

        Args:
            comment: Comment dictionary from GitHub API

        Returns:
            True if the comment is from CodeRabbit
        """
        user = comment.get("user", {})
        if isinstance(user, str):
            return user == self.coderabbit_author
        return user.get("login", "") == self.coderabbit_author

    def _group_into_threads(self, comments: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group comments into conversation threads.

        Args:
            comments: List of comments to group

        Returns:
            List of comment threads (each thread is a list of comments)
        """
        threads = {}

        for comment in comments:
            # Use file path and line number as thread identifier for inline comments
            path = comment.get("path", "")
            line = comment.get("line") or comment.get("original_line") or 0
            position = comment.get("position", 0)

            # For review-level comments, use PR number as identifier
            if not path:
                thread_id = "review"
            else:
                thread_id = f"{path}:{line}:{position}"

            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(comment)

        # Sort each thread by creation time
        for thread_id in threads:
            threads[thread_id].sort(key=lambda c: c.get("created_at", ""))

        return list(threads.values())

    def _filter_unresolved_threads(self, threads: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Filter out resolved comment threads.

        Args:
            threads: List of comment threads

        Returns:
            Flattened list of comments from unresolved threads
        """
        unresolved_comments = []

        for thread in threads:
            if not self.is_resolved(thread):
                unresolved_comments.extend(thread)

        return unresolved_comments

    def _extract_summary_comments(self, comments: List[Dict[str, Any]]) -> List[SummaryComment]:
        """Extract and process summary comments from CodeRabbit.

        Args:
            comments: List of PR-level comments

        Returns:
            List of processed summary comments
        """
        summary_comments = []

        for comment in comments:
            body = comment.get("body", "")

            # Use SummaryProcessor to check if this is a summary comment
            if self.summary_processor._is_summary_comment(body):
                try:
                    # Process the summary comment using SummaryProcessor
                    summary_comment = self.summary_processor.process_summary_comment(comment)
                    summary_comments.append(summary_comment)
                except CommentParsingError:
                    # If processing fails, fall back to basic summary comment
                    summary_comments.append(SummaryComment(raw_content=body))
            elif self.summary_processor.has_summary_content(body):
                # If it has summary-like content but isn't a formal summary
                summary_comments.append(SummaryComment(raw_content=body))

        return summary_comments

    def _extract_actionable_comments(self, comments: List[Dict[str, Any]]) -> List[ActionableComment]:
        """Extract actionable comments that require developer attention.

        Args:
            comments: List of unresolved comments

        Returns:
            List of actionable comments with priority classification
        """
        actionable_comments = []

        for comment in comments:
            body = comment.get("body", "")

            # Determine priority based on content patterns
            priority = self._determine_priority(body)

            # Extract actionable items from the comment
            action_items = self._extract_action_items(body)

            if action_items or priority != "info":
                # Map priority to enum values
                if priority == "critical":
                    priority = "high"  # Map critical to high as critical is not in enum
                elif priority == "info":
                    priority = "low"  # Map info to low

                # Create required fields for ActionableComment
                comment_id = str(comment.get("id", ""))
                file_path = comment.get("path", "")
                line_number = comment.get("line") or comment.get("position", 0)
                line_range = f"{line_number}" if line_number else "0"
                issue_description = self._extract_issue_description(body)

                actionable_comments.append(ActionableComment(
                    comment_id=comment_id,
                    file_path=file_path,
                    line_range=line_range,
                    issue_description=issue_description,
                    priority=priority,
                    raw_content=body
                ))

        return actionable_comments

    def _determine_priority(self, body: str) -> str:
        """Determine the priority level of a comment based on its content.

        Args:
            body: Comment body text

        Returns:
            Priority level: "critical", "high", "medium", "low", "info"
        """
        body_lower = body.lower()

        # Critical priority patterns
        critical_patterns = [
            "security", "vulnerability", "critical", "urgent", "breaking",
            "セキュリティ", "脆弱性", "重要", "緊急", "致命的"
        ]

        # High priority patterns
        high_patterns = [
            "error", "bug", "issue", "problem", "failure", "fix",
            "エラー", "バグ", "問題", "不具合", "修正"
        ]

        # Medium priority patterns
        medium_patterns = [
            "improvement", "optimize", "refactor", "performance",
            "改善", "最適化", "リファクタリング", "性能"
        ]

        # Low priority patterns
        low_patterns = [
            "style", "formatting", "convention", "documentation",
            "スタイル", "フォーマット", "規約", "ドキュメント"
        ]

        if any(pattern in body_lower for pattern in critical_patterns):
            return "critical"
        elif any(pattern in body_lower for pattern in high_patterns):
            return "high"
        elif any(pattern in body_lower for pattern in medium_patterns):
            return "medium"
        elif any(pattern in body_lower for pattern in low_patterns):
            return "low"
        else:
            return "info"

    def _extract_action_items(self, body: str) -> List[str]:
        """Extract specific action items from comment body.

        Args:
            body: Comment body text

        Returns:
            List of extracted action items
        """
        action_items = []

        # Look for common action patterns
        action_patterns = [
            r"(?:Please|Consider|Should|Need to|Must)\s+([^.!?]+)",
            r"(?:してください|考慮してください|すべきです|する必要があります)\s*([^。！？]+)",
            r"```suggestion\s*\n([^`]+)```",
            r"<!-- suggestion_start -->.*?```suggestion\s*\n([^`]+)```.*?<!-- suggestion_end -->"
        ]

        for pattern in action_patterns:
            matches = re.finditer(pattern, body, re.DOTALL | re.IGNORECASE)
            for match in matches:
                action_item = match.group(1).strip()
                if action_item and len(action_item) > 5:  # Filter out very short matches
                    action_items.append(action_item)

        return action_items

    def _categorize_comment(self, body: str) -> str:
        """Categorize the type of comment based on its content.

        Args:
            body: Comment body text

        Returns:
            Comment category: "refactor", "security", "performance", "style", "documentation", "general"
        """
        body_lower = body.lower()

        if any(word in body_lower for word in ["refactor", "リファクタリング", "restructure"]):
            return "refactor"
        elif any(word in body_lower for word in ["security", "セキュリティ", "vulnerability", "脆弱性"]):
            return "security"
        elif any(word in body_lower for word in ["performance", "性能", "optimize", "最適化"]):
            return "performance"
        elif any(word in body_lower for word in ["style", "format", "スタイル", "フォーマット"]):
            return "style"
        elif any(word in body_lower for word in ["documentation", "ドキュメント"]) and not any(word in body_lower for word in ["comment", "コメント"]):
            return "documentation"
        else:
            return "general"

    def _extract_issue_description(self, body: str) -> str:
        """Extract a concise issue description from comment body.

        Args:
            body: Full comment body text

        Returns:
            Concise issue description (first meaningful sentence)
        """
        # Remove HTML/markdown formatting
        import re
        clean_body = re.sub(r'<[^>]+>', '', body)
        clean_body = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', clean_body)
        clean_body = re.sub(r'`([^`]+)`', r'\1', clean_body)

        # Split into sentences and find the first meaningful one
        sentences = re.split(r'[.!?]\s+', clean_body.strip())

        for sentence in sentences:
            sentence = sentence.strip()
            # Skip very short sentences or common prefixes
            if len(sentence) > 20 and not sentence.startswith('_') and not sentence.startswith('<'):
                return sentence[:100] + '...' if len(sentence) > 100 else sentence

        # Fallback to first 100 characters
        return clean_body[:100] + '...' if len(clean_body) > 100 else clean_body

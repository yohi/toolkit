"""Unit tests for CommentAnalyzer class."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from coderabbit_fetcher.analyzer.comment_analyzer import CommentAnalyzer
from coderabbit_fetcher.models import AnalyzedComments, SummaryComment, ActionableComment
from coderabbit_fetcher.exceptions import CommentParsingError


class TestCommentAnalyzer:
    """Test cases for CommentAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CommentAnalyzer()

        # Sample CodeRabbit comment
        self.coderabbit_comment = {
            "id": 123456,
            "user": {"login": "coderabbitai[bot]"},
            "created_at": "2025-08-28T10:00:00Z",
            "body": "This is a CodeRabbit suggestion for improvement.",
            "path": "src/main.py",
            "line": 42,
            "position": 5
        }

        # Sample user comment
        self.user_comment = {
            "id": 123457,
            "user": {"login": "developer"},
            "created_at": "2025-08-28T11:00:00Z",
            "body": "Thanks for the review!",
            "path": "src/main.py",
            "line": 42,
            "position": 5
        }

        # Sample resolved comment
        self.resolved_comment = {
            "id": 123458,
            "user": {"login": "coderabbitai[bot]"},
            "created_at": "2025-08-28T12:00:00Z",
            "body": "Great fix! 🔒 CODERABBIT_RESOLVED 🔒",
            "path": "src/main.py",
            "line": 42,
            "position": 5
        }

        # Sample summary comment
        self.summary_comment = {
            "id": 123459,
            "user": {"login": "coderabbitai[bot]"},
            "created_at": "2025-08-28T09:00:00Z",
            "body": "## Summary by CodeRabbit\n\nThis PR includes several improvements...",
            "path": None
        }

    def test_is_coderabbit_comment_with_dict_user(self):
        """Test CodeRabbit comment identification with dict user."""
        assert self.analyzer._is_coderabbit_comment(self.coderabbit_comment) is True
        assert self.analyzer._is_coderabbit_comment(self.user_comment) is False

    def test_is_coderabbit_comment_with_string_user(self):
        """Test CodeRabbit comment identification with string user."""
        comment_with_string_user = {
            "id": 123460,
            "user": "coderabbitai[bot]",
            "body": "Test comment"
        }
        assert self.analyzer._is_coderabbit_comment(comment_with_string_user) is True

        comment_with_other_user = {
            "id": 123461,
            "user": "developer",
            "body": "Test comment"
        }
        assert self.analyzer._is_coderabbit_comment(comment_with_other_user) is False

    def test_filter_coderabbit_comments(self):
        """Test filtering to include only CodeRabbit comments."""
        comments = [
            self.coderabbit_comment,
            self.user_comment,
            self.resolved_comment,
            self.summary_comment
        ]

        filtered = self.analyzer.filter_coderabbit_comments(comments)

        assert len(filtered) == 3
        assert all(self.analyzer._is_coderabbit_comment(comment) for comment in filtered)
        assert self.user_comment not in filtered

    def test_is_resolved_with_resolved_thread(self):
        """Test resolution detection with resolved marker."""
        thread = [
            self.coderabbit_comment,
            self.user_comment,
            self.resolved_comment
        ]

        assert self.analyzer.is_resolved(thread) is True

    def test_is_resolved_with_unresolved_thread(self):
        """Test resolution detection without resolved marker."""
        thread = [
            self.coderabbit_comment,
            self.user_comment
        ]

        assert self.analyzer.is_resolved(thread) is False

    def test_is_resolved_with_empty_thread(self):
        """Test resolution detection with empty thread."""
        assert self.analyzer.is_resolved([]) is False

    def test_group_into_threads(self):
        """Test grouping comments into conversation threads."""
        comments = [
            self.coderabbit_comment,
            {**self.user_comment, "path": "src/main.py", "line": 42, "position": 5},
            {**self.coderabbit_comment, "id": 999, "path": "src/other.py", "line": 10}
        ]

        threads = self.analyzer._group_into_threads(comments)

        assert len(threads) == 2  # Two different file locations
        # First thread should have 2 comments (same file:line:position)
        assert len(threads[0]) == 2 or len(threads[1]) == 2
        # Second thread should have 1 comment
        assert len(threads[0]) == 1 or len(threads[1]) == 1

    def test_filter_unresolved_threads(self):
        """Test filtering out resolved threads."""
        # Create resolved thread
        resolved_thread = [
            self.coderabbit_comment,
            self.resolved_comment
        ]

        # Create unresolved thread
        unresolved_thread = [
            {**self.coderabbit_comment, "id": 999, "path": "other.py"}
        ]

        threads = [resolved_thread, unresolved_thread]
        unresolved = self.analyzer._filter_unresolved_threads(threads)

        assert len(unresolved) == 1
        assert unresolved[0]["id"] == 999

    def test_determine_priority_critical(self):
        """Test priority determination for critical issues."""
        critical_body = "This is a critical security vulnerability that needs immediate attention."
        assert self.analyzer._determine_priority(critical_body) == "critical"

        critical_japanese = "これは重要なセキュリティの脆弱性です。"
        assert self.analyzer._determine_priority(critical_japanese) == "critical"

    def test_determine_priority_high(self):
        """Test priority determination for high priority issues."""
        high_body = "This code has a bug that causes errors in production."
        assert self.analyzer._determine_priority(high_body) == "high"

        high_japanese = "このコードにはバグがあり、問題を引き起こします。"
        assert self.analyzer._determine_priority(high_japanese) == "high"

    def test_determine_priority_medium(self):
        """Test priority determination for medium priority issues."""
        medium_body = "Consider refactoring this code for better performance."
        assert self.analyzer._determine_priority(medium_body) == "medium"

        medium_japanese = "性能改善のためにリファクタリングを検討してください。"
        assert self.analyzer._determine_priority(medium_japanese) == "medium"

    def test_determine_priority_low(self):
        """Test priority determination for low priority issues."""
        low_body = "Please update the style formatting and follow coding conventions."
        assert self.analyzer._determine_priority(low_body) == "low"

        low_japanese = "スタイルガイドに従ってフォーマットを更新してください。"
        assert self.analyzer._determine_priority(low_japanese) == "low"

    def test_determine_priority_info(self):
        """Test priority determination for informational comments."""
        info_body = "This is just an informational note about the implementation."
        assert self.analyzer._determine_priority(info_body) == "info"

    def test_extract_action_items(self):
        """Test extraction of action items from comment body."""
        body_with_actions = """
        Please update the documentation for this function.
        Consider adding error handling here.
        ```suggestion
        def improved_function():
            pass
        ```
        """

        action_items = self.analyzer._extract_action_items(body_with_actions)

        assert len(action_items) >= 2
        assert any("documentation" in item for item in action_items)
        assert any("error handling" in item for item in action_items)

    def test_categorize_comment(self):
        """Test comment categorization."""
        assert self.analyzer._categorize_comment("Refactor this function") == "refactor"
        assert self.analyzer._categorize_comment("Security vulnerability found") == "security"
        assert self.analyzer._categorize_comment("Optimize performance here") == "performance"
        assert self.analyzer._categorize_comment("Fix code style issues") == "style"
        assert self.analyzer._categorize_comment("Add documentation here") == "documentation"
        assert self.analyzer._categorize_comment("General comment about the code") == "general"

    def test_extract_summary_comments(self):
        """Test extraction of summary comments."""
        comments = [
            self.summary_comment,
            self.coderabbit_comment
        ]

        summary_comments = self.analyzer._extract_summary_comments(comments)

        assert len(summary_comments) == 1
        assert isinstance(summary_comments[0], SummaryComment)
        assert self.summary_comment["body"] in summary_comments[0].raw_content

    def test_extract_actionable_comments(self):
        """Test extraction of actionable comments."""
        comments = [
            {**self.coderabbit_comment, "body": "Critical security issue needs immediate fix"},
            {**self.coderabbit_comment, "id": 999, "body": "Just an informational note"}
        ]

        actionable = self.analyzer._extract_actionable_comments(comments)

        assert len(actionable) >= 1
        assert actionable[0].priority == "high"  # critical maps to high
        assert isinstance(actionable[0], ActionableComment)

    def test_analyze_comments_success(self):
        """Test successful comment analysis."""
        comments_data = {
            "inline_comments": [self.coderabbit_comment, self.user_comment],
            "review_comments": [self.resolved_comment],
            "pr_comments": [self.summary_comment]
        }

        result = self.analyzer.analyze_comments(comments_data)

        assert isinstance(result, AnalyzedComments)
        assert result.metadata.total_comments > 0
        assert len(result.summary_comments) == 1
        assert result.metadata.processed_at is not None

    def test_analyze_comments_with_missing_data(self):
        """Test comment analysis with missing data fields."""
        comments_data = {
            "inline_comments": [self.coderabbit_comment]
            # Missing review_comments and pr_comments
        }

        result = self.analyzer.analyze_comments(comments_data)

        assert isinstance(result, AnalyzedComments)
        assert result.metadata.total_comments >= 0

    def test_analyze_comments_with_invalid_data(self):
        """Test comment analysis with invalid data."""
        invalid_data = {
            "inline_comments": "invalid_format"  # Should be list
        }

        with pytest.raises(CommentParsingError):
            self.analyzer.analyze_comments(invalid_data)

    def test_custom_resolved_marker(self):
        """Test using a custom resolved marker."""
        custom_marker = "✅ RESOLVED ✅"
        analyzer = CommentAnalyzer(resolved_marker=custom_marker)

        resolved_comment = {
            "id": 123,
            "user": {"login": "coderabbitai[bot]"},
            "created_at": "2025-08-28T12:00:00Z",
            "body": f"Fixed! {custom_marker}",
        }

        thread = [self.coderabbit_comment, resolved_comment]
        assert analyzer.is_resolved(thread) is True

    def test_thread_chronological_ordering(self):
        """Test that comments in threads are sorted chronologically."""
        # Create comments with different timestamps
        early_comment = {**self.coderabbit_comment, "created_at": "2025-08-28T09:00:00Z"}
        late_comment = {**self.resolved_comment, "created_at": "2025-08-28T15:00:00Z"}
        middle_comment = {**self.user_comment, "created_at": "2025-08-28T12:00:00Z"}

        # Add them in random order
        comments = [late_comment, early_comment, middle_comment]
        threads = self.analyzer._group_into_threads(comments)

        # Should be sorted by created_at
        thread = threads[0]  # All should be in same thread (same path/line)
        timestamps = [comment["created_at"] for comment in thread]
        assert timestamps == sorted(timestamps)

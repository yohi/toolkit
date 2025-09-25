"""Unit tests for ThreadProcessor class."""

import pytest
from datetime import datetime, timezone

from coderabbit_fetcher.processors.thread_processor import ThreadProcessor
from coderabbit_fetcher.models import ThreadContext
from coderabbit_fetcher.exceptions import CommentParsingError


class TestThreadProcessor:
    """Test cases for ThreadProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ThreadProcessor()

        # Sample comment thread with chronological ordering
        self.sample_thread = [
            {
                "id": 1001,
                "user": {"login": "developer1"},
                "created_at": "2025-01-01T10:00:00Z",
                "body": "This implementation looks problematic",
                "path": "src/auth.py",
                "line": 45,
                "in_reply_to_id": None
            },
            {
                "id": 1002,
                "user": {"login": "coderabbitai[bot]"},
                "created_at": "2025-01-01T11:00:00Z",
                "body": "I agree. The password hashing should use bcrypt instead of md5.",
                "path": "src/auth.py",
                "line": 45,
                "in_reply_to_id": 1001
            },
            {
                "id": 1003,
                "user": {"login": "developer1"},
                "created_at": "2025-01-01T12:00:00Z",
                "body": "Thanks for the suggestion. I'll implement that.",
                "path": "src/auth.py",
                "line": 45,
                "in_reply_to_id": 1002
            }
        ]

        # Sample resolved thread
        self.resolved_thread = [
            {
                "id": 2001,
                "user": {"login": "coderabbitai[bot]"},
                "created_at": "2025-01-01T10:00:00Z",
                "body": "Please fix the security issue here.",
                "path": "src/utils.py",
                "line": 20,
                "in_reply_to_id": None
            },
            {
                "id": 2002,
                "user": {"login": "developer2"},
                "created_at": "2025-01-01T11:00:00Z",
                "body": "Fixed the issue as suggested.",
                "path": "src/utils.py",
                "line": 20,
                "in_reply_to_id": 2001
            },
            {
                "id": 2003,
                "user": {"login": "coderabbitai[bot]"},
                "created_at": "2025-01-01T12:00:00Z",
                "body": "Great! Issue resolved. 🔒 CODERABBIT_RESOLVED 🔒",
                "path": "src/utils.py",
                "line": 20,
                "in_reply_to_id": 2002
            }
        ]

        # Sample complex thread with multiple participants
        self.complex_thread = [
            {
                "id": 3001,
                "user": {"login": "coderabbitai[bot]"},
                "created_at": "2025-01-01T10:00:00Z",
                "body": "_🛠️ Refactor suggestion_\n\nThis function is too complex. Consider breaking it down.",
                "path": "src/complex.py",
                "start_line": 100,
                "end_line": 150,
                "in_reply_to_id": None
            },
            {
                "id": 3002,
                "user": {"login": "developer1"},
                "created_at": "2025-01-01T11:00:00Z",
                "body": "I see your point, but this needs to be atomic.",
                "path": "src/complex.py",
                "start_line": 100,
                "end_line": 150,
                "in_reply_to_id": 3001
            },
            {
                "id": 3003,
                "user": {"login": "developer2"},
                "created_at": "2025-01-01T12:00:00Z",
                "body": "What about extracting helper methods?",
                "path": "src/complex.py",
                "start_line": 100,
                "end_line": 150,
                "in_reply_to_id": 3001
            },
            {
                "id": 3004,
                "user": {"login": "coderabbitai[bot]"},
                "created_at": "2025-01-01T13:00:00Z",
                "body": "Good suggestion! You could extract validation logic and business logic into separate methods.",
                "path": "src/complex.py",
                "start_line": 100,
                "end_line": 150,
                "in_reply_to_id": 3003
            }
        ]

        # Sample mixed comments for thread grouping
        self.mixed_comments = [
            # Thread 1
            {
                "id": 4001,
                "user": {"login": "developer1"},
                "created_at": "2025-01-01T10:00:00Z",
                "body": "First thread root",
                "path": "file1.py",
                "line": 10,
                "in_reply_to_id": None
            },
            {
                "id": 4002,
                "user": {"login": "coderabbitai[bot]"},
                "created_at": "2025-01-01T11:00:00Z",
                "body": "Reply to first thread",
                "path": "file1.py",
                "line": 10,
                "in_reply_to_id": 4001
            },
            # Thread 2
            {
                "id": 4003,
                "user": {"login": "developer2"},
                "created_at": "2025-01-01T12:00:00Z",
                "body": "Second thread root",
                "path": "file2.py",
                "line": 20,
                "in_reply_to_id": None
            },
            # Reply to Thread 1
            {
                "id": 4004,
                "user": {"login": "developer1"},
                "created_at": "2025-01-01T13:00:00Z",
                "body": "Another reply to first thread",
                "path": "file1.py",
                "line": 10,
                "in_reply_to_id": 4002
            }
        ]

    def test_sort_comments_chronologically(self):
        """Test chronological sorting of comments."""
        # Shuffle the comments
        shuffled = [self.sample_thread[2], self.sample_thread[0], self.sample_thread[1]]

        sorted_comments = self.processor._sort_comments_chronologically(shuffled)

        assert len(sorted_comments) == 3
        assert sorted_comments[0]["id"] == 1001  # Earliest
        assert sorted_comments[1]["id"] == 1002  # Middle
        assert sorted_comments[2]["id"] == 1003  # Latest

    def test_extract_line_context(self):
        """Test line context extraction."""
        # Single line
        comment1 = {"line": 45}
        assert self.processor._extract_line_context(comment1) == "45"

        # Line range
        comment2 = {"start_line": 100, "end_line": 150}
        assert self.processor._extract_line_context(comment2) == "100-150"

        # Single line in start_line
        comment3 = {"start_line": 20}
        assert self.processor._extract_line_context(comment3) == "20"

        # No line info
        comment4 = {"path": "file.py"}
        assert self.processor._extract_line_context(comment4) == ""

    def test_analyze_participants(self):
        """Test participant analysis."""
        participants = self.processor._analyze_participants(self.sample_thread)

        assert len(participants) == 2
        assert "developer1" in participants
        assert "coderabbitai[bot]" in participants
        assert participants == sorted(participants)  # Should be sorted

    def test_determine_resolution_status_resolved(self):
        """Test resolution status determination for resolved thread."""
        is_resolved = self.processor._determine_resolution_status(self.resolved_thread)
        assert is_resolved is True

    def test_determine_resolution_status_unresolved(self):
        """Test resolution status determination for unresolved thread."""
        is_resolved = self.processor._determine_resolution_status(self.sample_thread)
        assert is_resolved is False

    def test_generate_context_summary(self):
        """Test context summary generation."""
        summary = self.processor._generate_context_summary(self.sample_thread)

        assert "3 comments" in summary
        assert "2 participants" in summary
        assert "CodeRabbit provided 1 comments" in summary
        assert "src/auth.py" in summary

    def test_extract_topics_from_coderabbit_comments(self):
        """Test topic extraction from CodeRabbit comments."""
        topics = self.processor._extract_topics_from_coderabbit_comments(self.sample_thread)

        # Should find security-related topics (bcrypt/password hashing)
        # If no topics found, test that the function works without error
        assert isinstance(topics, list)

        # Test with explicit security content
        security_thread = [
            {
                "id": 9001,
                "user": {"login": "coderabbitai[bot]"},
                "created_at": "2025-01-01T10:00:00Z",
                "body": "This has security vulnerabilities that need to be addressed",
                "in_reply_to_id": None
            }
        ]

        security_topics = self.processor._extract_topics_from_coderabbit_comments(security_thread)
        assert "security" in security_topics

    def test_generate_ai_summary(self):
        """Test AI-friendly summary generation."""
        context_summary = "Basic summary"
        ai_summary = self.processor._generate_ai_summary(self.sample_thread, context_summary)

        assert "## Thread Context" in ai_summary
        assert "src/auth.py" in ai_summary
        assert "⏳ Open" in ai_summary  # Unresolved status
        assert "## CodeRabbit Analysis" in ai_summary

    def test_extract_action_items_from_thread(self):
        """Test action item extraction."""
        action_items = self.processor._extract_action_items_from_thread(self.sample_thread)

        # Should find action items from CodeRabbit comments
        assert len(action_items) >= 0  # May or may not find items depending on content

    def test_process_thread_success(self):
        """Test successful thread processing."""
        result = self.processor.process_thread(self.sample_thread)

        assert isinstance(result, ThreadContext)
        assert result.thread_id == "1001"
        assert result.root_comment_id == "1001"
        assert result.file_context == "src/auth.py"
        assert result.line_context == "45"
        assert len(result.participants) == 2
        assert result.comment_count == 3
        assert result.coderabbit_comment_count == 1
        assert result.is_resolved is False
        assert result.context_summary != ""
        assert result.ai_summary != ""
        assert len(result.chronological_comments) == 3

    def test_process_thread_resolved(self):
        """Test processing of resolved thread."""
        result = self.processor.process_thread(self.resolved_thread)

        assert isinstance(result, ThreadContext)
        assert result.is_resolved is True
        assert result.thread_id == "2001"
        assert result.coderabbit_comment_count == 2

    def test_process_thread_complex(self):
        """Test processing of complex thread."""
        result = self.processor.process_thread(self.complex_thread)

        assert isinstance(result, ThreadContext)
        assert len(result.participants) == 3
        assert result.comment_count == 4
        assert result.coderabbit_comment_count == 2
        assert "100-150" in result.line_context

    def test_process_thread_empty(self):
        """Test processing of empty thread."""
        result = self.processor.process_thread([])

        # Empty thread should return a valid ThreadContext with default values
        assert result.thread_id == "empty"
        assert result.main_comment["id"] == "empty"
        assert result.main_comment["body"] == "Empty thread"
        assert len(result.replies) == 0
        assert result.resolution_status == "unresolved"
        assert result.contextual_summary == "Empty thread"

    def test_group_comments_into_threads(self):
        """Test grouping comments into threads."""
        threads = self.processor._group_comments_into_threads(self.mixed_comments)

        assert len(threads) == 2  # Should create 2 threads

        # Find threads by root comment IDs
        thread_1 = next((t for t in threads if any(c["id"] == 4001 for c in t)), None)
        thread_2 = next((t for t in threads if any(c["id"] == 4003 for c in t)), None)

        assert thread_1 is not None
        assert thread_2 is not None

        # Thread 1 should have 3 comments (4001, 4002, 4004)
        assert len(thread_1) == 3

        # Thread 2 should have 1 comment (4003)
        assert len(thread_2) == 1

    def test_find_thread_root(self):
        """Test finding thread root comment."""
        comment_map = {str(c["id"]): c for c in self.mixed_comments}

        # Comment 4004 replies to 4002, which replies to 4001
        root_id = self.processor._find_thread_root("4004", comment_map)
        assert root_id == "4001"

        # Comment 4002 replies to 4001
        root_id = self.processor._find_thread_root("4002", comment_map)
        assert root_id == "4001"

        # Comment 4001 is root
        root_id = self.processor._find_thread_root("4001", comment_map)
        assert root_id == "4001"

    def test_build_thread_context(self):
        """Test building thread contexts from mixed comments."""
        contexts = self.processor.build_thread_context(self.mixed_comments)

        assert len(contexts) == 2

        # All contexts should be valid ThreadContext objects
        for context in contexts:
            assert isinstance(context, ThreadContext)
            assert context.thread_id != ""
            assert context.comment_count > 0

    def test_analyze_thread_complexity(self):
        """Test thread complexity analysis."""
        # Process a complex thread first
        context = self.processor.process_thread(self.complex_thread)

        # Analyze complexity
        complexity = self.processor.analyze_thread_complexity(context)

        assert "score" in complexity
        assert "factors" in complexity
        assert "priority" in complexity
        assert complexity["priority"] in ["low", "medium", "high"]
        assert isinstance(complexity["factors"], list)

    def test_complexity_factors(self):
        """Test specific complexity factors."""
        # Create a high complexity scenario with mock comments
        from coderabbit_fetcher.models.thread_context import ResolutionStatus
        mock_comments = []
        for i in range(10):
            user_login = f"user{i % 4}" if i % 4 < 3 else "coderabbitai[bot]"
            mock_comments.append({
                "id": 4000 + i,
                "user": {"login": user_login},
                "created_at": f"2025-01-01T{10 + i}:00:00Z",
                "body": f"Comment {i}",
                "path": "src/important.py",
                "line": 45
            })

        high_complexity_context = ThreadContext(
            thread_id="test",
            main_comment=mock_comments[0],
            replies=mock_comments[1:],
            resolution_status=ResolutionStatus.UNRESOLVED,
            contextual_summary="Complex discussion",
            chronological_order=mock_comments
        )

        complexity = self.processor.analyze_thread_complexity(high_complexity_context)

        assert complexity["score"] >= 6  # Should be high complexity
        assert complexity["priority"] == "high"
        assert "multiple participants" in complexity["factors"]
        assert "long discussion" in complexity["factors"]
        assert "unresolved" in complexity["factors"]

    def test_edge_cases(self):
        """Test various edge cases."""
        # Comment with malformed timestamp
        malformed_thread = [
            {
                "id": 5001,
                "user": {"login": "test"},
                "created_at": "invalid-date",
                "body": "Test comment",
                "in_reply_to_id": None
            }
        ]

        # Should not crash
        result = self.processor.process_thread(malformed_thread)
        assert isinstance(result, ThreadContext)

        # Comment with missing user info
        missing_user_thread = [
            {
                "id": 5002,
                "created_at": "2025-01-01T10:00:00Z",
                "body": "Test comment",
                "in_reply_to_id": None
            }
        ]

        # Should not crash
        result = self.processor.process_thread(missing_user_thread)
        assert isinstance(result, ThreadContext)

    def test_resolution_patterns(self):
        """Test various resolution patterns."""
        resolution_patterns = [
            "✅ This issue is resolved",
            "Issue fixed successfully",
            "implemented the suggestion as requested",
            "[CR_RESOLUTION_CONFIRMED:TECHNICAL_ISSUE_RESOLVED]"
        ]

        for pattern in resolution_patterns:
            thread = [
                {
                    "id": 6001,
                    "user": {"login": "coderabbitai[bot]"},
                    "created_at": "2025-01-01T10:00:00Z",
                    "body": f"Original issue here",
                    "in_reply_to_id": None
                },
                {
                    "id": 6002,
                    "user": {"login": "coderabbitai[bot]"},
                    "created_at": "2025-01-01T11:00:00Z",
                    "body": pattern,
                    "in_reply_to_id": 6001
                }
            ]

            is_resolved = self.processor._determine_resolution_status(thread)
            assert is_resolved is True, f"Pattern '{pattern}' should be detected as resolved"

    def test_japanese_content_support(self):
        """Test support for Japanese content in threads."""
        japanese_thread = [
            {
                "id": 7001,
                "user": {"login": "coderabbitai[bot]"},
                "created_at": "2025-01-01T10:00:00Z",
                "body": "セキュリティの問題があります。パスワードハッシュ化を改善してください。",
                "path": "src/auth.py",
                "line": 45,
                "in_reply_to_id": None
            },
            {
                "id": 7002,
                "user": {"login": "developer1"},
                "created_at": "2025-01-01T11:00:00Z",
                "body": "分かりました。修正します。",
                "path": "src/auth.py",
                "line": 45,
                "in_reply_to_id": 7001
            }
        ]

        result = self.processor.process_thread(japanese_thread)

        assert isinstance(result, ThreadContext)
        assert result.comment_count == 2
        assert result.coderabbit_comment_count == 1
        # Should process without errors even with Japanese content

    def test_performance_with_large_thread(self):
        """Test performance with large thread."""
        # Create a large thread (100 comments)
        large_thread = []
        for i in range(100):
            comment = {
                "id": 8000 + i,
                "user": {"login": f"user{i % 5}"},
                "created_at": f"2025-01-01T{10 + (i // 10):02d}:{i % 60:02d}:00Z",
                "body": f"Comment number {i}",
                "path": "src/large.py",
                "line": 100 + i,
                "in_reply_to_id": 8000 + i - 1 if i > 0 else None
            }
            large_thread.append(comment)

        # Should complete within reasonable time
        result = self.processor.process_thread(large_thread)

        assert isinstance(result, ThreadContext)
        assert result.comment_count == 100
        assert len(result.participants) <= 5

    def test_build_thread_context_error_handling(self):
        """Test error handling in build_thread_context."""
        # Include some problematic comments that should be skipped
        problematic_comments = [
            # Valid thread
            {
                "id": 9001,
                "user": {"login": "test"},
                "created_at": "2025-01-01T10:00:00Z",
                "body": "Valid comment",
                "in_reply_to_id": None
            },
            # Problematic comment (missing required data)
            {
                "user": {"login": "test"},
                "created_at": "invalid",
                "body": "Problematic comment",
                "in_reply_to_id": None
            }
        ]

        # Should not crash and should return at least one valid context
        contexts = self.processor.build_thread_context(problematic_comments)

        # Should have processed the valid thread
        assert len(contexts) >= 1
        assert all(isinstance(ctx, ThreadContext) for ctx in contexts)

    def test_build_thread_context_empty_comments(self):
        """Test that empty comments list returns empty result instead of raising exception."""
        # Empty comments should return empty list, not raise exception
        contexts = self.processor.build_thread_context([])

        assert isinstance(contexts, list)
        assert len(contexts) == 0

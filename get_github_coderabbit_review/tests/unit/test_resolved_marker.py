"""Unit tests for resolved marker management."""

import pytest
from unittest.mock import Mock, patch

from coderabbit_fetcher.resolved_marker import (
    ResolvedMarkerConfig,
    ResolvedMarkerDetector,
    ResolvedMarkerManager
)
from coderabbit_fetcher.models import ThreadContext, ResolutionStatus


class TestResolvedMarkerConfig:
    """Test cases for ResolvedMarkerConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ResolvedMarkerConfig()
        
        assert config.default_marker == "🔒 CODERABBIT_RESOLVED 🔒"
        assert config.case_sensitive is True
        assert config.exact_match is True
        assert isinstance(config.additional_patterns, list)
        assert len(config.additional_patterns) > 0
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ResolvedMarkerConfig(
            default_marker="CUSTOM_RESOLVED",
            case_sensitive=False,
            exact_match=False,
            additional_patterns=["PATTERN1", "PATTERN2"]
        )
        
        assert config.default_marker == "CUSTOM_RESOLVED"
        assert config.case_sensitive is False
        assert config.exact_match is False
        assert "PATTERN1" in config.additional_patterns
        assert "PATTERN2" in config.additional_patterns
    
    def test_all_patterns_property(self):
        """Test all_patterns property includes default and additional."""
        config = ResolvedMarkerConfig(
            additional_patterns=["EXTRA1", "EXTRA2"]
        )
        
        patterns = config.all_patterns
        assert config.default_marker in patterns
        assert "EXTRA1" in patterns
        assert "EXTRA2" in patterns
    
    def test_compiled_patterns_case_sensitive(self):
        """Test compiled patterns with case sensitivity."""
        config = ResolvedMarkerConfig(
            default_marker="RESOLVED",
            case_sensitive=True,
            additional_patterns=[]
        )
        
        compiled = config.get_compiled_patterns()
        assert len(compiled) == 1
        
        # Test case sensitivity
        pattern = compiled[0]
        assert pattern.search("RESOLVED") is not None
        assert pattern.search("resolved") is None
    
    def test_compiled_patterns_case_insensitive(self):
        """Test compiled patterns without case sensitivity."""
        config = ResolvedMarkerConfig(
            default_marker="RESOLVED",
            case_sensitive=False,
            additional_patterns=[]
        )
        
        compiled = config.get_compiled_patterns()
        pattern = compiled[0]
        
        assert pattern.search("RESOLVED") is not None
        assert pattern.search("resolved") is not None
        assert pattern.search("Resolved") is not None
    
    def test_exact_match_patterns(self):
        """Test exact match pattern generation."""
        config = ResolvedMarkerConfig(
            default_marker="RESOLVED",
            exact_match=True,
            additional_patterns=[]
        )
        
        compiled = config.get_compiled_patterns()
        pattern = compiled[0]
        
        # Should match exact word
        assert pattern.search("RESOLVED") is not None
        assert pattern.search("word RESOLVED word") is not None
        
        # Should not match partial
        assert pattern.search("UNRESOLVED") is None
        assert pattern.search("RESOLVEDMORE") is None


class TestResolvedMarkerDetector:
    """Test cases for ResolvedMarkerDetector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ResolvedMarkerConfig(
            default_marker="🔒 RESOLVED 🔒",
            additional_patterns=["RESOLVED_BY_CR", "✅ DONE"],
            case_sensitive=True,
            exact_match=True
        )
        self.detector = ResolvedMarkerDetector(self.config)
    
    def test_default_detector(self):
        """Test detector with default configuration."""
        detector = ResolvedMarkerDetector()
        assert detector.config.default_marker == "🔒 CODERABBIT_RESOLVED 🔒"
    
    def test_is_comment_resolved_with_marker(self):
        """Test comment resolution detection with resolved marker."""
        comment = {"body": "This issue is fixed. 🔒 RESOLVED 🔒"}
        assert self.detector.is_comment_resolved(comment) is True
    
    def test_is_comment_resolved_without_marker(self):
        """Test comment resolution detection without resolved marker."""
        comment = {"body": "This issue needs attention."}
        assert self.detector.is_comment_resolved(comment) is False
    
    def test_is_comment_resolved_with_additional_pattern(self):
        """Test comment resolution detection with additional pattern."""
        comment = {"body": "Fixed the issue. RESOLVED_BY_CR"}
        assert self.detector.is_comment_resolved(comment) is True
        
        comment2 = {"body": "Task completed ✅ DONE"}
        assert self.detector.is_comment_resolved(comment2) is True
    
    def test_is_comment_resolved_different_content_fields(self):
        """Test comment resolution with different content field names."""
        # Test 'content' field
        comment1 = {"content": "Fixed! 🔒 RESOLVED 🔒"}
        assert self.detector.is_comment_resolved(comment1) is True
        
        # Test string comment
        comment2 = "Resolved the issue. 🔒 RESOLVED 🔒"
        assert self.detector.is_comment_resolved(comment2) is True
        
        # Test object with body attribute
        comment3 = Mock()
        comment3.body = "Done! 🔒 RESOLVED 🔒"
        assert self.detector.is_comment_resolved(comment3) is True
    
    def test_is_comment_resolved_empty_comment(self):
        """Test resolution detection with empty comment."""
        assert self.detector.is_comment_resolved({}) is False
        assert self.detector.is_comment_resolved(None) is False
        assert self.detector.is_comment_resolved("") is False
    
    def test_is_thread_resolved_with_resolved_coderabbit_comment(self):
        """Test thread resolution with resolved CodeRabbit comment."""
        thread_comments = [
            {"user": {"login": "developer"}, "body": "Found an issue"},
            {"user": {"login": "coderabbitai"}, "body": "Here's the problem"},
            {"user": {"login": "developer"}, "body": "Fixed it"},
            {"user": {"login": "coderabbitai"}, "body": "Looks good! 🔒 RESOLVED 🔒"}
        ]
        
        assert self.detector.is_thread_resolved(thread_comments) is True
    
    def test_is_thread_resolved_without_resolved_marker(self):
        """Test thread resolution without resolved marker."""
        thread_comments = [
            {"user": {"login": "developer"}, "body": "Found an issue"},
            {"user": {"login": "coderabbitai"}, "body": "Here's the problem"},
            {"user": {"login": "developer"}, "body": "Fixed it"},
            {"user": {"login": "coderabbitai"}, "body": "Thanks for the fix!"}
        ]
        
        assert self.detector.is_thread_resolved(thread_comments) is False
    
    def test_is_thread_resolved_no_coderabbit_comments(self):
        """Test thread resolution with no CodeRabbit comments."""
        thread_comments = [
            {"user": {"login": "developer1"}, "body": "Found an issue"},
            {"user": {"login": "developer2"}, "body": "I'll fix it"},
            {"user": {"login": "developer1"}, "body": "Thanks!"}
        ]
        
        assert self.detector.is_thread_resolved(thread_comments) is False
    
    def test_is_thread_resolved_empty_thread(self):
        """Test thread resolution with empty thread."""
        assert self.detector.is_thread_resolved([]) is False
        assert self.detector.is_thread_resolved(None) is False
    
    def test_detect_resolution_status_resolved(self):
        """Test resolution status detection for resolved thread."""
        thread = ThreadContext(
            thread_id="test_123",
            main_comment={"body": "Initial comment"},
            replies=[],
            resolution_status=ResolutionStatus.UNRESOLVED,
            chronological_order=[
                {"user": {"login": "coderabbitai"}, "body": "Issue fixed! 🔒 RESOLVED 🔒"}
            ],
            contextual_summary="Test thread",
            root_comment_id="root_123"
        )
        
        status = self.detector.detect_resolution_status(thread)
        assert status == ResolutionStatus.RESOLVED
    
    def test_detect_resolution_status_unresolved(self):
        """Test resolution status detection for unresolved thread."""
        thread = ThreadContext(
            thread_id="test_124",
            main_comment={"body": "Initial comment"},
            replies=[],
            resolution_status=ResolutionStatus.UNRESOLVED,
            chronological_order=[
                {"user": {"login": "coderabbitai"}, "body": "Found an issue"}
            ],
            contextual_summary="Test thread",
            root_comment_id="root_124"
        )
        
        status = self.detector.detect_resolution_status(thread)
        assert status == ResolutionStatus.UNRESOLVED
    
    def test_detect_resolution_status_fallback_main_comment(self):
        """Test resolution status detection falling back to main comment."""
        thread = ThreadContext(
            thread_id="test_125",
            main_comment={"body": "Fixed! 🔒 RESOLVED 🔒"},
            replies=[],
            resolution_status=ResolutionStatus.UNRESOLVED,
            chronological_order=[],
            contextual_summary="Test thread",
            root_comment_id="root_125"
        )
        
        status = self.detector.detect_resolution_status(thread)
        assert status == ResolutionStatus.RESOLVED
    
    def test_filter_resolved_comments(self):
        """Test filtering resolved comments from list."""
        comments = [
            {"body": "Issue 1"},
            {"body": "Issue 2 - 🔒 RESOLVED 🔒"},
            {"body": "Issue 3"},
            {"body": "Issue 4 - RESOLVED_BY_CR"}
        ]
        
        unresolved = self.detector.filter_resolved_comments(comments)
        
        assert len(unresolved) == 2
        assert unresolved[0]["body"] == "Issue 1"
        assert unresolved[1]["body"] == "Issue 3"
    
    def test_filter_resolved_threads(self):
        """Test filtering resolved threads from list."""
        threads = [
            ThreadContext(
                thread_id="thread_1",
                main_comment={"body": "Issue 1"},
                replies=[],
                resolution_status=ResolutionStatus.UNRESOLVED,
                chronological_order=[],
                contextual_summary="Thread 1",
                root_comment_id="root_1"
            ),
            ThreadContext(
                thread_id="thread_2",
                main_comment={"body": "Issue 2 - 🔒 RESOLVED 🔒"},
                replies=[],
                resolution_status=ResolutionStatus.UNRESOLVED,
                chronological_order=[],
                contextual_summary="Thread 2",
                root_comment_id="root_2"
            ),
            ThreadContext(
                thread_id="thread_3",
                main_comment={"body": "Issue 3"},
                replies=[],
                resolution_status=ResolutionStatus.UNRESOLVED,
                chronological_order=[],
                contextual_summary="Thread 3",
                root_comment_id="root_3"
            )
        ]
        
        unresolved = self.detector.filter_resolved_threads(threads)
        
        assert len(unresolved) == 2
        assert unresolved[0].thread_id == "thread_1"
        assert unresolved[1].thread_id == "thread_3"
    
    def test_get_resolution_statistics(self):
        """Test resolution statistics calculation."""
        comments = [
            {"body": "Issue 1"},
            {"body": "Issue 2 - 🔒 RESOLVED 🔒"},
            {"body": "Issue 3"},
            {"body": "Issue 4 - ✅ DONE"},
            {"body": "Issue 5"}
        ]
        
        stats = self.detector.get_resolution_statistics(comments)
        
        assert stats["total_comments"] == 5
        assert stats["resolved_comments"] == 2
        assert stats["unresolved_comments"] == 3
        assert stats["resolution_rate"] == 0.4
    
    def test_get_resolution_statistics_empty(self):
        """Test resolution statistics with empty comment list."""
        stats = self.detector.get_resolution_statistics([])
        
        assert stats["total_comments"] == 0
        assert stats["resolved_comments"] == 0
        assert stats["unresolved_comments"] == 0
        assert stats["resolution_rate"] == 0.0
    
    def test_is_coderabbit_comment_various_formats(self):
        """Test CodeRabbit comment detection with various formats."""
        # Standard format
        comment1 = {"user": {"login": "coderabbitai"}}
        assert self.detector._is_coderabbit_comment(comment1) is True
        
        # Bot format
        comment2 = {"user": {"login": "coderabbitai[bot]"}}
        assert self.detector._is_coderabbit_comment(comment2) is True
        
        # Author field
        comment3 = {"author": "coderabbitai"}
        assert self.detector._is_coderabbit_comment(comment3) is True
        
        # Node ID pattern
        comment4 = {"node_id": "coderabbitai_123456"}
        assert self.detector._is_coderabbit_comment(comment4) is True
        
        # Not CodeRabbit
        comment5 = {"user": {"login": "developer"}}
        assert self.detector._is_coderabbit_comment(comment5) is False
    
    def test_false_positive_prevention(self):
        """Test prevention of false positive marker detection."""
        # Should not match partial words
        comment1 = {"body": "This is unresolved issue"}
        assert self.detector.is_comment_resolved(comment1) is False
        
        # Should not match without proper boundaries
        comment2 = {"body": "The resolvedissue needs attention"}
        assert self.detector.is_comment_resolved(comment2) is False
        
        # Should match exact marker
        comment3 = {"body": "Issue is 🔒 RESOLVED 🔒 now"}
        assert self.detector.is_comment_resolved(comment3) is True


class TestResolvedMarkerManager:
    """Test cases for ResolvedMarkerManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ResolvedMarkerConfig(
            default_marker="🔒 TEST_RESOLVED 🔒",
            additional_patterns=["TEST_DONE"]
        )
        self.manager = ResolvedMarkerManager(self.config)
    
    def test_default_manager(self):
        """Test manager with default configuration."""
        manager = ResolvedMarkerManager()
        assert manager.config.default_marker == "🔒 CODERABBIT_RESOLVED 🔒"
    
    def test_process_comments_with_resolution(self):
        """Test comment processing with resolution filtering."""
        comments = [
            {"body": "Issue 1"},
            {"body": "Issue 2 - 🔒 TEST_RESOLVED 🔒"},
            {"body": "Issue 3"},
            {"body": "Issue 4 - TEST_DONE"}
        ]
        
        result = self.manager.process_comments_with_resolution(comments)
        
        assert len(result["original_comments"]) == 4
        assert len(result["unresolved_comments"]) == 2
        assert result["statistics"]["total_comments"] == 4
        assert result["statistics"]["resolved_comments"] == 2
        assert result["statistics"]["unresolved_comments"] == 2
        assert result["statistics"]["resolution_rate"] == 0.5
        
        # Check marker config is included
        assert "marker_config" in result
        assert result["marker_config"]["default_marker"] == "🔒 TEST_RESOLVED 🔒"
    
    def test_process_threads_with_resolution(self):
        """Test thread processing with resolution status update."""
        threads = [
            ThreadContext(
                thread_id="thread_1",
                main_comment={"body": "Issue 1"},
                replies=[],
                resolution_status=ResolutionStatus.UNRESOLVED,
                chronological_order=[],
                contextual_summary="Thread 1",
                root_comment_id="root_1"
            ),
            ThreadContext(
                thread_id="thread_2",
                main_comment={"body": "Issue 2 - 🔒 TEST_RESOLVED 🔒"},
                replies=[],
                resolution_status=ResolutionStatus.UNRESOLVED,
                chronological_order=[],
                contextual_summary="Thread 2",
                root_comment_id="root_2"
            )
        ]
        
        result = self.manager.process_threads_with_resolution(threads)
        
        assert len(result["original_threads"]) == 2
        assert len(result["unresolved_threads"]) == 1
        assert result["statistics"]["total_threads"] == 2
        assert result["statistics"]["resolved_threads"] == 1
        assert result["statistics"]["unresolved_threads"] == 1
        assert result["statistics"]["resolution_rate"] == 0.5
        
        # Check that resolution status was updated
        assert result["original_threads"][1].resolution_status == ResolutionStatus.RESOLVED
    
    def test_update_config(self):
        """Test configuration update."""
        original_marker = self.manager.config.default_marker
        
        self.manager.update_config(
            default_marker="NEW_MARKER",
            case_sensitive=False
        )
        
        assert self.manager.config.default_marker == "NEW_MARKER"
        assert self.manager.config.case_sensitive is False
        
        # Verify detector was recreated
        assert self.manager.detector.config.default_marker == "NEW_MARKER"
    
    def test_add_custom_marker(self):
        """Test adding custom marker."""
        original_count = len(self.manager.config.additional_patterns)
        
        self.manager.add_custom_marker("CUSTOM_MARKER")
        
        assert len(self.manager.config.additional_patterns) == original_count + 1
        assert "CUSTOM_MARKER" in self.manager.config.additional_patterns
        
        # Test duplicate prevention
        self.manager.add_custom_marker("CUSTOM_MARKER")
        assert len(self.manager.config.additional_patterns) == original_count + 1
    
    def test_validate_marker_good(self):
        """Test marker validation with good marker."""
        result = self.manager.validate_marker("🔒 CODERABBIT_RESOLVED_UNIQUE 🔒")
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["uniqueness_score"] > 0.5
    
    def test_validate_marker_bad(self):
        """Test marker validation with problematic marker."""
        result = self.manager.validate_marker("ok")
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert "Marker too short" in result["issues"][0]
        assert len(result["recommendations"]) > 0
    
    def test_validate_marker_with_common_words(self):
        """Test marker validation with common words."""
        result = self.manager.validate_marker("the issue is resolved")
        
        assert result["valid"] is False
        assert any("common words" in issue for issue in result["issues"])
    
    def test_uniqueness_score_calculation(self):
        """Test uniqueness score calculation."""
        # Short marker
        short_score = self.manager._calculate_uniqueness_score("OK")
        
        # Long unique marker
        unique_score = self.manager._calculate_uniqueness_score("🔒 VERY_UNIQUE_CODERABBIT_RESOLVED_MARKER_123 🔒")
        
        # Medium marker
        medium_score = self.manager._calculate_uniqueness_score("RESOLVED_CR")
        
        assert unique_score > medium_score > short_score
        assert 0.0 <= short_score <= 1.0
        assert 0.0 <= medium_score <= 1.0
        assert 0.0 <= unique_score <= 1.0


class TestResolvedMarkerIntegration:
    """Integration tests for resolved marker functionality."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from raw comments to filtered output."""
        # Setup
        config = ResolvedMarkerConfig(
            default_marker="🔒 INTEGRATION_RESOLVED 🔒"
        )
        manager = ResolvedMarkerManager(config)
        
        # Raw comments data (simulating GitHub API response)
        raw_comments = [
            {
                "user": {"login": "developer1"},
                "body": "Found a bug in the authentication logic"
            },
            {
                "user": {"login": "coderabbitai"},
                "body": "I see the issue. Here's what needs to be fixed..."
            },
            {
                "user": {"login": "developer1"},
                "body": "Thanks! I've applied your suggestions."
            },
            {
                "user": {"login": "coderabbitai"},
                "body": "Great! The fix looks good. 🔒 INTEGRATION_RESOLVED 🔒"
            },
            {
                "user": {"login": "developer2"},
                "body": "Another issue with error handling"
            },
            {
                "user": {"login": "coderabbitai"},
                "body": "This needs attention..."
            }
        ]
        
        # Process comments
        result = manager.process_comments_with_resolution(raw_comments)
        
        # Verify results
        assert result["statistics"]["total_comments"] == 6
        assert result["statistics"]["resolved_comments"] == 1  # Only the CodeRabbit comment with marker
        assert result["statistics"]["unresolved_comments"] == 5
        
        # Check that resolved comment is filtered out
        unresolved_bodies = [c["body"] for c in result["unresolved_comments"]]
        assert "Great! The fix looks good. 🔒 INTEGRATION_RESOLVED 🔒" not in unresolved_bodies
        assert "Another issue with error handling" in unresolved_bodies
    
    def test_thread_context_integration(self):
        """Test integration with ThreadContext objects."""
        config = ResolvedMarkerConfig()
        manager = ResolvedMarkerManager(config)
        
        # Create thread contexts
        threads = [
            # Unresolved thread
            ThreadContext(
                thread_id="unresolved_thread",
                main_comment={"body": "Bug report"},
                replies=[
                    {"user": {"login": "coderabbitai"}, "body": "Analysis..."},
                    {"user": {"login": "developer"}, "body": "Working on it"}
                ],
                resolution_status=ResolutionStatus.UNRESOLVED,
                chronological_order=[
                    {"user": {"login": "developer"}, "body": "Bug report"},
                    {"user": {"login": "coderabbitai"}, "body": "Analysis..."},
                    {"user": {"login": "developer"}, "body": "Working on it"}
                ],
                contextual_summary="Bug discussion",
                root_comment_id="root_unresolved"
            ),
            
            # Resolved thread
            ThreadContext(
                thread_id="resolved_thread",
                main_comment={"body": "Another bug"},
                replies=[
                    {"user": {"login": "coderabbitai"}, "body": "Fixed! 🔒 CODERABBIT_RESOLVED 🔒"}
                ],
                resolution_status=ResolutionStatus.UNRESOLVED,  # Will be updated
                chronological_order=[
                    {"user": {"login": "developer"}, "body": "Another bug"},
                    {"user": {"login": "coderabbitai"}, "body": "Fixed! 🔒 CODERABBIT_RESOLVED 🔒"}
                ],
                contextual_summary="Fixed bug discussion",
                root_comment_id="root_resolved"
            )
        ]
        
        # Process threads
        result = manager.process_threads_with_resolution(threads)
        
        # Verify results
        assert result["statistics"]["total_threads"] == 2
        assert result["statistics"]["resolved_threads"] == 1
        assert result["statistics"]["unresolved_threads"] == 1
        
        # Check resolution status was updated
        resolved_thread = next(t for t in result["original_threads"] if t.thread_id == "resolved_thread")
        assert resolved_thread.resolution_status == ResolutionStatus.RESOLVED
        
        # Check filtering
        unresolved_thread_ids = [t.thread_id for t in result["unresolved_threads"]]
        assert "unresolved_thread" in unresolved_thread_ids
        assert "resolved_thread" not in unresolved_thread_ids
    
    def test_multiple_marker_patterns(self):
        """Test detection with multiple marker patterns."""
        config = ResolvedMarkerConfig(
            default_marker="🔒 PRIMARY 🔒",
            additional_patterns=["SECONDARY_RESOLVED", "✅ TERTIARY ✅"]
        )
        detector = ResolvedMarkerDetector(config)
        
        test_cases = [
            ("Fixed! 🔒 PRIMARY 🔒", True),
            ("Done. SECONDARY_RESOLVED", True),
            ("Complete ✅ TERTIARY ✅", True),
            ("Still working on it", False),
            ("The primary concern is...", False),  # Partial match should not work
            ("SECONDARY_RESOLVED_BUT_MORE", False)  # Partial match should not work
        ]
        
        for content, expected in test_cases:
            comment = {"body": content}
            result = detector.is_comment_resolved(comment)
            assert result == expected, f"Failed for content: {content}"
    
    def test_performance_with_large_datasets(self):
        """Test performance with large number of comments."""
        config = ResolvedMarkerConfig()
        detector = ResolvedMarkerDetector(config)
        
        # Generate large dataset
        import time
        
        large_comments = []
        for i in range(1000):
            marker = "🔒 CODERABBIT_RESOLVED 🔒" if i % 10 == 0 else ""
            large_comments.append({
                "body": f"Comment {i} content here. {marker}"
            })
        
        # Measure performance
        start_time = time.time()
        stats = detector.get_resolution_statistics(large_comments)
        end_time = time.time()
        
        # Verify results
        assert stats["total_comments"] == 1000
        assert stats["resolved_comments"] == 100  # Every 10th comment
        assert stats["unresolved_comments"] == 900
        
        # Performance should be reasonable (less than 1 second for 1000 comments)
        processing_time = end_time - start_time
        assert processing_time < 1.0, f"Processing took too long: {processing_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

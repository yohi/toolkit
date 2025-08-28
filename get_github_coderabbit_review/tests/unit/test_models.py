"""
Unit tests for data models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from coderabbit_fetcher.models import (
    AnalyzedComments,
    CommentMetadata,
    SummaryComment,
    ReviewComment,
    ActionableComment,
    AIAgentPrompt,
    ThreadContext,
    ChangeEntry,
    CommentType,
    Priority,
    ResolutionStatus,
)


class TestCommentMetadata:
    """Test CommentMetadata model."""
    
    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = CommentMetadata(
            pr_number=123,
            pr_title="Test PR",
            owner="testowner",
            repo="testrepo",
            total_comments=10,
            coderabbit_comments=5,
            resolved_comments=2,
            actionable_comments=3,
            processing_time_seconds=1.5,
        )
        
        assert metadata.pr_number == 123
        assert metadata.resolution_rate == 0.4  # 2/5
        assert metadata.actionable_rate == 0.6  # 3/5
        assert isinstance(metadata.processed_at, datetime)
    
    def test_zero_coderabbit_comments(self):
        """Test metadata with zero CodeRabbit comments."""
        metadata = CommentMetadata(
            pr_number=123,
            pr_title="Test PR",
            owner="testowner",
            repo="testrepo",
            total_comments=10,
            coderabbit_comments=0,
            resolved_comments=0,
            actionable_comments=0,
            processing_time_seconds=1.5,
        )
        
        assert metadata.resolution_rate == 0.0
        assert metadata.actionable_rate == 0.0


class TestAIAgentPrompt:
    """Test AIAgentPrompt model."""
    
    def test_python_detection(self):
        """Test Python language detection."""
        prompt = AIAgentPrompt(
            code_block="def hello():\n    print('hello')",
            description="Test function",
        )
        
        assert prompt.language == "python"
        assert prompt.is_complete_suggestion
    
    def test_javascript_detection(self):
        """Test JavaScript language detection."""
        prompt = AIAgentPrompt(
            code_block="function hello() {\n    console.log('hello');\n}",
            description="Test function",
        )
        
        assert prompt.language == "javascript"
    
    def test_short_code_block(self):
        """Test short code block is not considered complete."""
        prompt = AIAgentPrompt(
            code_block="x = 1",
            description="Simple assignment",
        )
        
        assert not prompt.is_complete_suggestion


class TestActionableComment:
    """Test ActionableComment model."""
    
    def test_priority_detection_high(self):
        """Test high priority detection."""
        comment = ActionableComment(
            comment_id="123",
            file_path="test.py",
            line_range="10-15",
            issue_description="Security vulnerability found",
            raw_content="This is a critical security issue",
        )
        
        assert comment.priority == Priority.HIGH
        assert comment.is_high_priority
    
    def test_priority_detection_low(self):
        """Test low priority detection."""
        comment = ActionableComment(
            comment_id="123",
            file_path="test.py",
            line_range="10-15",
            issue_description="Minor style issue",
            raw_content="This is a nitpick comment about formatting",
        )
        
        assert comment.priority == Priority.LOW
        assert not comment.is_high_priority
    
    def test_comment_type_detection(self):
        """Test comment type detection."""
        comment = ActionableComment(
            comment_id="123",
            file_path="test.py",
            line_range="10-15",
            issue_description="Test issue",
            raw_content="🧹 Nitpick comments (1)",
        )
        
        assert comment.comment_type == CommentType.NITPICK


class TestThreadContext:
    """Test ThreadContext model."""
    
    def test_basic_thread(self):
        """Test basic thread creation."""
        thread = ThreadContext(
            main_comment={"user": {"login": "user1"}, "created_at": "2023-01-01T10:00:00Z"},
            thread_id="thread123",
        )
        
        assert thread.participant_count == 1
        assert "user1" in thread.contextual_summary
        assert thread.resolution_status == ResolutionStatus.UNRESOLVED
    
    def test_thread_with_replies(self):
        """Test thread with replies."""
        thread = ThreadContext(
            main_comment={"user": {"login": "user1"}, "created_at": "2023-01-01T10:00:00Z"},
            replies=[
                {"user": {"login": "user2"}, "created_at": "2023-01-01T11:00:00Z"},
                {"user": {"login": "user1"}, "created_at": "2023-01-01T12:00:00Z"},
            ],
            thread_id="thread123",
        )
        
        assert thread.participant_count == 2
        assert len(thread.chronological_order) == 3
        assert "user2" in thread.contextual_summary


class TestSummaryComment:
    """Test SummaryComment model."""
    
    def test_empty_summary(self):
        """Test empty summary comment."""
        summary = SummaryComment(raw_content="Empty summary")
        
        assert not summary.has_new_features
        assert not summary.has_documentation_changes
        assert not summary.has_test_changes
        assert summary.total_changes == 0
    
    def test_full_summary(self):
        """Test summary with all types of changes."""
        summary = SummaryComment(
            new_features=["Feature 1", "Feature 2"],
            documentation_changes=["Doc update"],
            test_changes=["Test added"],
            changes_table=[
                ChangeEntry(cohort_or_files="file1.py", summary="Added function"),
            ],
            raw_content="Full summary",
        )
        
        assert summary.has_new_features
        assert summary.has_documentation_changes
        assert summary.has_test_changes
        assert summary.total_changes == 4


class TestAnalyzedComments:
    """Test AnalyzedComments model."""
    
    def test_empty_analysis(self):
        """Test empty analysis result."""
        metadata = CommentMetadata(
            pr_number=123,
            pr_title="Test PR",
            owner="testowner",
            repo="testrepo",
            total_comments=0,
            coderabbit_comments=0,
            resolved_comments=0,
            actionable_comments=0,
            processing_time_seconds=0.1,
        )
        
        analysis = AnalyzedComments(metadata=metadata)
        
        assert not analysis.has_summary
        assert not analysis.has_actionable_items
        assert analysis.total_actionable_items == 0
        assert "No significant CodeRabbit feedback found" in analysis.get_summary_text()
    
    def test_full_analysis(self):
        """Test analysis with all types of content."""
        metadata = CommentMetadata(
            pr_number=123,
            pr_title="Test PR",
            owner="testowner",
            repo="testrepo",
            total_comments=10,
            coderabbit_comments=5,
            resolved_comments=2,
            actionable_comments=3,
            processing_time_seconds=1.5,
        )
        
        summary = SummaryComment(
            new_features=["Feature 1"],
            raw_content="Summary content",
        )
        
        actionable_comment = ActionableComment(
            comment_id="123",
            file_path="test.py",
            line_range="10-15",
            issue_description="Test issue",
            raw_content="Test content",
            ai_agent_prompt=AIAgentPrompt(
                code_block="def test(): pass",
                description="Test prompt",
            ),
        )
        
        review = ReviewComment(
            actionable_count=1,
            actionable_comments=[actionable_comment],
            raw_content="Review content",
        )
        
        analysis = AnalyzedComments(
            summary_comments=[summary],
            review_comments=[review],
            metadata=metadata,
        )
        
        assert analysis.has_summary
        assert analysis.has_actionable_items
        assert analysis.has_ai_prompts
        assert analysis.total_actionable_items == 1
        assert "test.py" in analysis.files_with_issues

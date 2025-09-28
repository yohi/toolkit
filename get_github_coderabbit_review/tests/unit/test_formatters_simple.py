"""Simple test for formatters to verify basic functionality."""

import json
from datetime import datetime
from coderabbit_fetcher.formatters import MarkdownFormatter, JSONFormatter, PlainTextFormatter
from coderabbit_fetcher.models import AnalyzedComments, SummaryComment, CommentMetadata


def test_basic_markdown_formatter():
    """Test basic markdown formatter functionality."""
    formatter = MarkdownFormatter()
    persona = "You are a test reviewer."

    metadata = CommentMetadata(
        pr_number=123,
        pr_title="Test PR",
        owner="test",
        repo="test-repo",
        processed_at=datetime.now(),
        total_comments=1,
        coderabbit_comments=1,
        resolved_comments=0,
        actionable_comments=0,
        processing_time_seconds=1.0
    )

    comments = AnalyzedComments(
        summary_comments=[
            SummaryComment(
                new_features=["Test feature"],
                documentation_changes=[],
                test_changes=[],
                walkthrough="Test walkthrough",
                changes_table=[],
                raw_content="Test content"
            )
        ],
        review_comments=[],
        unresolved_threads=[],
        metadata=metadata
    )

    result = formatter.format(persona, comments)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "CodeRabbit Analysis Report" in result
    assert "Test feature" in result


def test_basic_json_formatter():
    """Test basic JSON formatter functionality."""
    formatter = JSONFormatter()
    persona = "You are a test reviewer."

    metadata = CommentMetadata(
        pr_number=124,
        pr_title="JSON Test PR",
        owner="test",
        repo="test-repo",
        total_comments=1,
        coderabbit_comments=1,
        resolved_comments=0,
        actionable_comments=0,
        processing_time_seconds=1.0
    )

    comments = AnalyzedComments(
        summary_comments=[
            SummaryComment(
                new_features=["JSON feature"],
                documentation_changes=[],
                test_changes=[],
                walkthrough="JSON walkthrough",
                changes_table=[],
                raw_content="JSON content"
            )
        ],
        review_comments=[],
        unresolved_threads=[],
        metadata=metadata
    )

    result = formatter.format(persona, comments)

    assert isinstance(result, str)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)
    assert "persona" in parsed
    assert "summary_comments" in parsed


def test_basic_plaintext_formatter():
    """Test basic plaintext formatter functionality."""
    formatter = PlainTextFormatter()
    persona = "You are a test reviewer."

    metadata = CommentMetadata(
        pr_number=125,
        pr_title="Plain Test PR",
        owner="test",
        repo="test-repo",
        total_comments=1,
        coderabbit_comments=1,
        resolved_comments=0,
        actionable_comments=0,
        processing_time_seconds=1.0
    )

    comments = AnalyzedComments(
        summary_comments=[
            SummaryComment(
                new_features=["Plain feature"],
                documentation_changes=[],
                test_changes=[],
                walkthrough="Plain walkthrough",
                changes_table=[],
                raw_content="Plain content"
            )
        ],
        review_comments=[],
        unresolved_threads=[],
        metadata=metadata
    )

    result = formatter.format(persona, comments)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "CODERABBIT ANALYSIS REPORT" in result
    assert "Plain feature" in result


if __name__ == "__main__":
    test_basic_markdown_formatter()
    test_basic_json_formatter()
    test_basic_plaintext_formatter()
    print("All basic formatter tests passed!")

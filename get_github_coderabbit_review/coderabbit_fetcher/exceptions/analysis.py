"""Comment analysis and processing exceptions."""

from typing import Optional

from .base import CodeRabbitFetcherError


class CommentAnalysisError(CodeRabbitFetcherError):
    """Exception raised when comment analysis fails."""

    def __init__(self, message: str, analysis_stage: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if analysis_stage:
            details["analysis_stage"] = analysis_stage

        super().__init__(
            message,
            details=details,
            suggestions=[
                "Check PR data format and structure",
                "Verify CodeRabbit comments are present",
                "Try with a different pull request",
            ],
            **kwargs,
        )


class CodeRabbitDetectionError(CommentAnalysisError):
    """Exception raised when CodeRabbit comment detection fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            analysis_stage="coderabbit_detection",
            suggestions=[
                "Verify the PR contains CodeRabbit comments",
                "Check comment author format (coderabbitai[bot])",
                "Ensure comments are properly formatted",
            ],
            **kwargs,
        )


class ThreadProcessingError(CommentAnalysisError):
    """Exception raised when comment thread processing fails."""

    def __init__(self, message: str, thread_id: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if thread_id:
            details["thread_id"] = thread_id

        super().__init__(
            message,
            analysis_stage="thread_processing",
            details=details,
            suggestions=[
                "Check comment thread structure",
                "Verify comment timestamps and IDs",
                "Try processing individual comments",
            ],
            **kwargs,
        )


class ResolvedMarkerError(CommentAnalysisError):
    """Exception raised when resolved marker processing fails."""

    def __init__(self, message: str, marker: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if marker:
            details["resolved_marker"] = marker

        super().__init__(
            message,
            analysis_stage="resolved_marker_processing",
            details=details,
            suggestions=[
                "Check resolved marker format and uniqueness",
                "Verify marker detection logic",
                "Use a more specific marker string",
            ],
            **kwargs,
        )


class CommentFilteringError(CommentAnalysisError):
    """Exception raised when comment filtering fails."""

    def __init__(self, message: str, filter_type: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if filter_type:
            details["filter_type"] = filter_type

        super().__init__(
            message,
            analysis_stage="comment_filtering",
            details=details,
            suggestions=[
                "Check filter criteria and logic",
                "Verify comment data structure",
                "Try with different filter settings",
            ],
            **kwargs,
        )


class SummaryProcessingError(CommentAnalysisError):
    """Exception raised when summary comment processing fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            analysis_stage="summary_processing",
            suggestions=[
                "Check summary comment format",
                "Verify 'Summary by CodeRabbit' header",
                "Check for parsing pattern issues",
            ],
            **kwargs,
        )


class ReviewProcessingError(CommentAnalysisError):
    """Exception raised when review comment processing fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            analysis_stage="review_processing",
            suggestions=[
                "Check review comment structure",
                "Verify actionable comment counts",
                "Check for review data inconsistencies",
            ],
            **kwargs,
        )

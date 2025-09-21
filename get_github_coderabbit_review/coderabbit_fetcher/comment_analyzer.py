"""Core comment analysis and filtering functionality."""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .exceptions import CodeRabbitFetcherError
from .models import (
    ActionableComment,
    AnalyzedComments,
    CommentMetadata,
    ResolutionStatus,
    ReviewComment,
    SummaryComment,
    ThreadContext,
)
from .processors import ReviewProcessor, SummaryProcessor, ThreadProcessor
from .resolved_marker import ResolvedMarkerConfig, ResolvedMarkerDetector

logger = logging.getLogger(__name__)


class CommentAnalysisError(CodeRabbitFetcherError):
    """Exception raised during comment analysis."""

    pass


@dataclass
class CommentStats:
    """Statistics collected during comment analysis."""

    total_comments: int = 0
    coderabbit_comments: int = 0
    summary_comments: int = 0
    review_comments: int = 0
    inline_comments: int = 0
    resolved_comments: int = 0
    actionable_comments: int = 0
    threads_processed: int = 0
    nitpick_comments: int = 0
    outside_diff_comments: int = 0
    additional_comments: int = 0
    processing_time_seconds: float = 0.0


class CommentAnalyzer:
    """Analyzes and categorizes CodeRabbit comments from GitHub PR data."""

    def __init__(self, resolved_marker_config: Optional[ResolvedMarkerConfig] = None):
        """Initialize comment analyzer.

        Args:
            resolved_marker_config: Configuration for resolved marker detection
        """
        self.resolved_marker_config = resolved_marker_config or ResolvedMarkerConfig()
        self.resolved_marker_detector = ResolvedMarkerDetector(self.resolved_marker_config)

        # Initialize processors
        self.summary_processor = SummaryProcessor()
        self.review_processor = ReviewProcessor()
        self.thread_processor = ThreadProcessor()

        # Statistics tracking
        self.stats = CommentStats()

    def analyze_comments(self, pr_data: Dict[str, Any]) -> AnalyzedComments:
        """Analyze pull request data and extract CodeRabbit comments.

        Args:
            pr_data: Pull request data from GitHub API

        Returns:
            Analyzed and categorized comments

        Raises:
            CommentAnalysisError: If analysis fails
        """
        start_time = time.time()

        try:
            # Reset statistics
            self.stats = CommentStats()

            # Extract basic PR information
            pr_info = self._extract_pr_info(pr_data)

            # Get all comments (issues + reviews)
            all_comments = self._collect_all_comments(pr_data)
            self.stats.total_comments = len(all_comments)

            # Filter CodeRabbit comments
            coderabbit_comments = self._filter_coderabbit_comments(all_comments)
            self.stats.coderabbit_comments = len(coderabbit_comments)

            if not coderabbit_comments:
                # Return empty result with metadata
                self.stats.processing_time_seconds = time.time() - start_time
                return self._create_empty_result(pr_info)

            # Categorize comments
            summary_comments, review_comments, inline_comments = self._categorize_comments(
                coderabbit_comments
            )

            # Process each category
            processed_summary = self._process_summary_comments(summary_comments)
            processed_review = self._process_review_comments(review_comments)
            processed_threads = self._process_thread_comments(inline_comments)

            # Extract actionable comments from inline comments
            inline_actionables = self._extract_inline_actionable_comments(inline_comments)

            # Collect all actionable comments from review comments
            all_actionables = []
            for review_comment in processed_review:
                all_actionables.extend(review_comment.actionable_comments)

            # Add inline actionables
            all_actionables.extend(inline_actionables)

            # Deduplicate actionable comments to match XML expectations
            deduplicated_actionables = self._deduplicate_actionable_comments(all_actionables)

            # Update review comments with deduplicated actionables
            # Clear existing actionables and redistribute deduplicated ones
            for review_comment in processed_review:
                review_comment.actionable_comments = []

            # Add deduplicated actionables to the first review comment if any exist
            if processed_review and deduplicated_actionables:
                processed_review[0].actionable_comments = deduplicated_actionables
                logger.debug(
                    f"Assigned {len(deduplicated_actionables)} deduplicated actionables to first review comment"
                )

            # Apply resolved marker filtering
            filtered_threads = self._filter_resolved_threads(processed_threads)

            # Create metadata
            metadata = self._create_metadata(pr_info)

            # Final statistics
            self.stats.processing_time_seconds = time.time() - start_time

            return AnalyzedComments(
                summary_comments=processed_summary,
                review_comments=processed_review,
                unresolved_threads=filtered_threads,
                metadata=metadata,
            )

        except Exception as e:
            raise CommentAnalysisError(f"Failed to analyze comments: {e}") from e

    def _extract_pr_info(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic pull request information."""
        return {
            "number": pr_data.get("number"),
            "title": pr_data.get("title", ""),
            "url": pr_data.get("url", ""),
            "owner": pr_data.get("owner", ""),
            "repo": pr_data.get("repo", ""),
            "state": pr_data.get("state", ""),
            "author": pr_data.get("author", {}).get("login", "") if pr_data.get("author") else "",
        }

    def _collect_all_comments(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect all comments from PR data (issues + reviews)."""
        all_comments = []

        # Add issue comments
        if "comments" in pr_data:
            for comment in pr_data["comments"]:
                comment["comment_type"] = "issue"
                all_comments.append(comment)

        # Add review comments
        if "reviews" in pr_data:
            for review in pr_data["reviews"]:
                # Add the review itself as a comment
                if "body" in review and review["body"]:
                    review_comment = {
                        "id": review.get("id"),
                        "body": review["body"],
                        "user": review.get("author", {}),  # GitHub API uses 'author' for reviews
                        "created_at": review.get(
                            "submittedAt"
                        ),  # GitHub API uses 'submittedAt' for reviews
                        "comment_type": "review",
                    }
                    all_comments.append(review_comment)

                # Add individual review comments
                if "comments" in review:
                    for comment in review["comments"]:
                        comment["comment_type"] = "review_comment"
                        all_comments.append(comment)

        return all_comments

    def _filter_coderabbit_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter comments to only include those from CodeRabbit."""
        coderabbit_comments = []

        for comment in comments:
            user = comment.get("user", {})
            if isinstance(user, dict):
                login = user.get("login", "").lower()
                if "coderabbitai" in login:
                    coderabbit_comments.append(comment)

        return coderabbit_comments

    def _categorize_comments(self, comments: List[Dict[str, Any]]) -> tuple:
        """Categorize CodeRabbit comments into summary, review, and inline types."""
        summary_comments = []
        review_comments = []
        inline_comments = []

        for comment in comments:
            body = comment.get("body", "")
            comment_type = comment.get("comment_type", "")
            comment_id = comment.get("id", "unknown")
            path = comment.get("path", "N/A")
            line = comment.get("line", "N/A")

            logger.debug(
                f"Categorizing comment {comment_id} | type: {comment_type} | path: {path}:{line}"
            )
            logger.debug(f"Body preview: {body[:100]}...")

            # Check if it's a summary comment
            if "Summary by CodeRabbit" in body or "## Summary" in body:
                logger.debug("-> SUMMARY comment")
                summary_comments.append(comment)
                self.stats.summary_comments += 1

            # Check if it's a review comment (actionable comments posted)
            elif "Actionable comments posted:" in body or comment_type == "review":
                logger.debug("-> REVIEW comment")
                review_comments.append(comment)
                self.stats.review_comments += 1

            # Otherwise treat as inline comment
            else:
                logger.debug("-> INLINE comment")
                inline_comments.append(comment)
                self.stats.inline_comments += 1

        return summary_comments, review_comments, inline_comments

    def _process_summary_comments(self, comments: List[Dict[str, Any]]) -> List[SummaryComment]:
        """Process summary comments using SummaryProcessor."""
        processed = []

        for comment in comments:
            try:
                summary = self.summary_processor.process_summary_comment(comment)
                processed.append(summary)
            except Exception as e:
                # Log error but continue processing
                import logging

                logging.warning(f"Failed to process summary comment {comment.get('id')}: {e}")

        return processed

    def _process_review_comments(self, comments: List[Dict[str, Any]]) -> List[ReviewComment]:
        """Process review comments using ReviewProcessor."""
        processed = []

        for comment in comments:
            try:
                review = self.review_processor.process_review_comment(comment)
                processed.append(review)
                self.stats.actionable_comments += review.actionable_count

                # Count nitpick, outside diff, and additional comments
                self.stats.nitpick_comments += len(review.nitpick_comments)
                self.stats.outside_diff_comments += len(review.outside_diff_comments)
                self.stats.additional_comments += len(review.additional_comments)

            except Exception as e:
                # Log error but continue processing
                import logging

                logging.warning(f"Failed to process review comment {comment.get('id')}: {e}")

        return processed

    def _process_thread_comments(self, comments: List[Dict[str, Any]]) -> List[ThreadContext]:
        """Process inline comments into thread contexts."""
        try:
            logger.debug(f"Processing {len(comments)} inline comments as threads")
            threads = self.thread_processor.build_thread_context(comments)
            logger.debug(f"Built {len(threads)} thread contexts")
            self.stats.threads_processed = len(threads)
            return threads
        except Exception as e:
            # Log error and return empty list
            import logging

            logging.warning(f"Failed to process thread comments: {e}")
            return []

    def _extract_inline_actionable_comments(self, inline_comments: List[Dict[str, Any]]) -> List:
        """Extract actionable comments from inline comments."""
        actionables = []

        logger.debug(f"Extracting actionable comments from {len(inline_comments)} inline comments")

        for comment in inline_comments:
            try:
                actionable = self.review_processor.extract_actionable_from_inline_comment(comment)
                if actionable:
                    actionables.append(actionable)
            except Exception as e:
                logger.debug(f"Error extracting actionable from inline comment: {e}")

        logger.debug(f"Extracted {len(actionables)} actionable comments from inline")
        return actionables

    def _deduplicate_actionable_comments(
        self, actionable_comments: List[ActionableComment]
    ) -> List[ActionableComment]:
        """Remove duplicate actionable comments based on comment_id and content.

        Args:
            actionable_comments: List of actionable comments that may contain duplicates

        Returns:
            Deduplicated list of actionable comments
        """
        seen_ids = set()
        seen_content = set()
        deduplicated = []

        for comment in actionable_comments:
            # Use comment_id as primary deduplication key
            if comment.comment_id in seen_ids:
                logger.debug(f"Skipping duplicate actionable comment ID: {comment.comment_id}")
                continue

            # Also check content similarity as fallback
            content_key = (comment.file_path, comment.line_range, comment.issue_description)
            if content_key in seen_content:
                logger.debug(f"Skipping duplicate actionable comment content: {content_key}")
                continue

            deduplicated.append(comment)
            seen_ids.add(comment.comment_id)
            seen_content.add(content_key)
            logger.debug(f"Added actionable comment: {comment.comment_id}")

        logger.debug(f"Deduplicated actionables: {len(actionable_comments)} -> {len(deduplicated)}")
        return deduplicated

    def _filter_resolved_threads(self, threads: List[ThreadContext]) -> List[ThreadContext]:
        """Filter out resolved threads using resolved marker detection."""
        if not threads:
            return []

        # Update resolution status for all threads
        for thread in threads:
            status = self.resolved_marker_detector.detect_resolution_status(thread)
            thread.resolution_status = status

            if status == ResolutionStatus.RESOLVED:
                self.stats.resolved_comments += 1

        # Filter to only unresolved threads
        unresolved = [
            thread for thread in threads if thread.resolution_status != ResolutionStatus.RESOLVED
        ]

        return unresolved

    def _create_metadata(self, pr_info: Dict[str, Any]) -> CommentMetadata:
        """Create metadata object with processing statistics."""
        return CommentMetadata(
            pr_number=pr_info["number"],
            pr_title=pr_info["title"],
            owner=pr_info["owner"],
            repo=pr_info["repo"],
            total_comments=self.stats.total_comments,
            coderabbit_comments=self.stats.coderabbit_comments,
            resolved_comments=self.stats.resolved_comments,
            actionable_comments=self.stats.actionable_comments,
            summary_comments=self.stats.summary_comments,
            review_comments=self.stats.review_comments,
            nitpick_comments=self.stats.nitpick_comments,
            outside_diff_comments=self.stats.outside_diff_comments,
            additional_comments=self.stats.additional_comments,
            thread_contexts=self.stats.threads_processed,
            processing_time_seconds=self.stats.processing_time_seconds,
        )

    def _create_empty_result(self, pr_info: Dict[str, Any]) -> AnalyzedComments:
        """Create empty result when no CodeRabbit comments found."""
        metadata = self._create_metadata(pr_info)

        return AnalyzedComments(
            summary_comments=[], review_comments=[], unresolved_threads=[], metadata=metadata
        )

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get detailed analysis statistics.

        Returns:
            Dictionary with analysis statistics
        """
        return {
            "total_comments": self.stats.total_comments,
            "coderabbit_comments": self.stats.coderabbit_comments,
            "summary_comments": self.stats.summary_comments,
            "review_comments": self.stats.review_comments,
            "inline_comments": self.stats.inline_comments,
            "resolved_comments": self.stats.resolved_comments,
            "actionable_comments": self.stats.actionable_comments,
            "nitpick_comments": self.stats.nitpick_comments,
            "outside_diff_comments": self.stats.outside_diff_comments,
            "additional_comments": self.stats.additional_comments,
            "threads_processed": self.stats.threads_processed,
            "processing_time_seconds": self.stats.processing_time_seconds,
            "resolution_rate": (
                self.stats.resolved_comments / self.stats.coderabbit_comments
                if self.stats.coderabbit_comments > 0
                else 0.0
            ),
        }

    def validate_pr_data(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PR data structure and content.

        Args:
            pr_data: Pull request data to validate

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "comment_count": 0,
            "review_count": 0,
        }

        # Check required fields
        if not isinstance(pr_data, dict):
            validation_result["valid"] = False
            validation_result["issues"].append("PR data must be a dictionary")
            return validation_result

        if "number" not in pr_data:
            validation_result["issues"].append("Missing PR number")
            validation_result["valid"] = False

        if "title" not in pr_data:
            validation_result["warnings"].append("Missing PR title")

        # Check comments structure
        if "comments" in pr_data:
            comments = pr_data["comments"]
            if isinstance(comments, list):
                validation_result["comment_count"] = len(comments)

                # Validate comment structure
                for i, comment in enumerate(comments):
                    if not isinstance(comment, dict):
                        validation_result["issues"].append(f"Comment {i} is not a dictionary")
                        validation_result["valid"] = False
                    elif "body" not in comment:
                        validation_result["warnings"].append(f"Comment {i} missing body")
            else:
                validation_result["issues"].append("Comments field must be a list")
                validation_result["valid"] = False

        # Check reviews structure
        if "reviews" in pr_data:
            reviews = pr_data["reviews"]
            if isinstance(reviews, list):
                validation_result["review_count"] = len(reviews)

                # Validate review structure
                for i, review in enumerate(reviews):
                    if not isinstance(review, dict):
                        validation_result["issues"].append(f"Review {i} is not a dictionary")
                        validation_result["valid"] = False
            else:
                validation_result["issues"].append("Reviews field must be a list")
                validation_result["valid"] = False

        # Check if any comments exist
        total_items = validation_result["comment_count"] + validation_result["review_count"]
        if total_items == 0:
            validation_result["warnings"].append("No comments or reviews found")

        return validation_result

    def update_resolved_marker_config(self, new_config: ResolvedMarkerConfig) -> None:
        """Update resolved marker configuration.

        Args:
            new_config: New resolved marker configuration
        """
        self.resolved_marker_config = new_config
        self.resolved_marker_detector = ResolvedMarkerDetector(new_config)

    def is_coderabbit_comment(self, comment: Dict[str, Any]) -> bool:
        """Check if a comment is from CodeRabbit.

        Args:
            comment: Comment object to check

        Returns:
            True if comment is from CodeRabbit
        """
        user = comment.get("user", {})
        if isinstance(user, dict):
            login = user.get("login", "").lower()
            return "coderabbitai" in login
        return False

    def analyze_comment_trends(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in CodeRabbit comments.

        Args:
            comments: List of comments to analyze

        Returns:
            Dictionary with trend analysis
        """
        trends = {
            "total_comments": len(comments),
            "coderabbit_percentage": 0.0,
            "comment_types": {},
            "resolution_patterns": {},
            "time_distribution": {},
        }

        if not comments:
            return trends

        coderabbit_count = 0
        comment_types = {}

        for comment in comments:
            # Count CodeRabbit comments
            if self.is_coderabbit_comment(comment):
                coderabbit_count += 1

                # Analyze comment type
                body = comment.get("body", "")
                if "Summary by CodeRabbit" in body:
                    comment_types["summary"] = comment_types.get("summary", 0) + 1
                elif "Actionable comments posted:" in body:
                    comment_types["review"] = comment_types.get("review", 0) + 1
                else:
                    comment_types["inline"] = comment_types.get("inline", 0) + 1

        trends["coderabbit_percentage"] = (coderabbit_count / len(comments)) * 100
        trends["comment_types"] = comment_types

        return trends

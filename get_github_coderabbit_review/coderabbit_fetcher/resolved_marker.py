"""Resolved marker management for CodeRabbit comments."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .models import ResolutionStatus, ThreadContext


@dataclass
class ResolvedMarkerConfig:
    """Configuration for resolved marker detection.

    Contains patterns and settings for detecting resolved comments
    from CodeRabbit's last replies.
    """

    # Default marker with emoji to prevent false positives
    default_marker: str = "🔒 CODERABBIT_RESOLVED 🔒"

    # Additional patterns to detect various resolution formats
    additional_patterns: Optional[List[str]] = None

    # Case sensitive matching (recommended for security)
    case_sensitive: bool = True

    # Require exact match (no partial matches)
    exact_match: bool = True

    def __post_init__(self) -> None:
        """Initialize additional patterns if not provided."""
        if self.additional_patterns is None:
            self.additional_patterns = [
                # Alternative formats that might be used
                "CODERABBIT_RESOLVED",
                "CodeRabbit: RESOLVED",
                "🔐 RESOLVED 🔐",
                "✅ CODERABBIT_RESOLVED ✅",
                # Format from requirements document
                "[CR_RESOLUTION_CONFIRMED]",
                "RESOLVED_BY_CODERABBIT",
            ]

    @property
    def all_patterns(self) -> List[str]:
        """Get all marker patterns including default and additional.

        Returns:
            List of all patterns to check for resolution
        """
        patterns = [self.default_marker]
        if self.additional_patterns:
            patterns.extend(self.additional_patterns)
        return patterns

    def get_compiled_patterns(self) -> List[re.Pattern]:
        """Get compiled regex patterns for efficient matching.

        Returns:
            List of compiled regex patterns
        """
        flags = 0 if self.case_sensitive else re.IGNORECASE
        compiled = []

        for pattern in self.all_patterns:
            escaped_pattern = re.escape(pattern)

            if self.exact_match:
                # For exact match, ensure pattern is surrounded by non-word chars or start/end of string
                # This handles emoji and special characters properly
                regex_pattern = f"(?:^|\\s|[^\\w]){escaped_pattern}(?:$|\\s|[^\\w])"
            else:
                # Allow partial matches (less secure)
                regex_pattern = escaped_pattern

            compiled.append(re.compile(regex_pattern, flags))

        return compiled


class ResolvedMarkerDetector:
    """Detector for resolved markers in CodeRabbit comments."""

    def __init__(self, config: Optional[ResolvedMarkerConfig] = None):
        """Initialize detector with configuration.

        Args:
            config: Optional configuration, uses default if not provided
        """
        self.config = config or ResolvedMarkerConfig()
        self._compiled_patterns: List[re.Pattern[str]] = self.config.get_compiled_patterns()

    def is_comment_resolved(self, comment: Dict[str, Any]) -> bool:
        """Check if a single comment contains resolved markers.

        Args:
            comment: Comment object to check

        Returns:
            True if comment contains resolved markers
        """
        content = self._extract_comment_content(comment)
        if not content:
            return False

        return self._contains_resolved_marker(content)

    def is_thread_resolved(self, thread_comments: List[Dict[str, Any]]) -> bool:
        """Check if a thread is resolved based on last CodeRabbit reply.

        Args:
            thread_comments: List of comments in thread (chronological order)

        Returns:
            True if thread is resolved based on last CodeRabbit comment
        """
        if not thread_comments:
            return False

        # Find the last CodeRabbit comment in the thread
        last_coderabbit_comment = self._find_last_coderabbit_comment(thread_comments)
        if not last_coderabbit_comment:
            return False

        return self.is_comment_resolved(last_coderabbit_comment)

    def detect_resolution_status(self, thread_context: ThreadContext) -> ResolutionStatus:
        """Detect resolution status for a thread context.

        Args:
            thread_context: Thread context to analyze

        Returns:
            Detected resolution status
        """
        # Check chronological order for resolved markers
        if thread_context.chronological_order:
            if self.is_thread_resolved(thread_context.chronological_order):
                return ResolutionStatus.RESOLVED

        # Check main comment if no chronological order
        if hasattr(thread_context, "main_comment") and thread_context.main_comment:
            if self.is_comment_resolved(thread_context.main_comment):
                return ResolutionStatus.RESOLVED

        # Check replies for resolved markers
        if hasattr(thread_context, "replies") and thread_context.replies:
            for reply in thread_context.replies:
                if self.is_comment_resolved(reply):
                    return ResolutionStatus.RESOLVED

        # Default to current resolution status or unresolved
        return getattr(thread_context, "resolution_status", ResolutionStatus.UNRESOLVED)

    def filter_resolved_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out resolved comments from a list.

        Args:
            comments: List of comments to filter

        Returns:
            List of unresolved comments
        """
        unresolved = []

        for comment in comments:
            if not self.is_comment_resolved(comment):
                unresolved.append(comment)

        return unresolved

    def filter_resolved_threads(self, threads: List[ThreadContext]) -> List[ThreadContext]:
        """Filter out resolved threads from a list.

        Args:
            threads: List of thread contexts to filter

        Returns:
            List of unresolved thread contexts
        """
        unresolved = []

        for thread in threads:
            status = self.detect_resolution_status(thread)
            if status != ResolutionStatus.RESOLVED:
                unresolved.append(thread)

        return unresolved

    def get_resolution_statistics(self, comments: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics about resolved vs unresolved comments.

        Args:
            comments: List of comments to analyze

        Returns:
            Dictionary with resolution statistics
        """
        total = len(comments)
        resolved = sum(1 for comment in comments if self.is_comment_resolved(comment))
        unresolved = total - resolved

        return {
            "total_comments": total,
            "resolved_comments": resolved,
            "unresolved_comments": unresolved,
            "resolution_rate": resolved / total if total > 0 else 0.0,
        }

    def _extract_comment_content(self, comment: Dict[str, Any]) -> str:
        """Extract text content from comment object.

        Args:
            comment: Comment object

        Returns:
            Comment text content
        """
        if isinstance(comment, dict):
            # Try common field names for comment content
            for field in ["body", "content", "text", "message"]:
                if field in comment and comment[field]:
                    return str(comment[field])
        elif isinstance(comment, str):
            return comment
        elif hasattr(comment, "body"):
            return str(comment.body)
        elif hasattr(comment, "content"):
            return str(comment.content)

        return ""

    def _contains_resolved_marker(self, content: str) -> bool:
        """Check if content contains any resolved markers.

        Args:
            content: Text content to check

        Returns:
            True if any resolved marker is found
        """
        if not content:
            return False

        # Simple string containment check for exact match mode
        if self.config.exact_match:
            for pattern in self.config.all_patterns:
                if pattern in content:
                    # Additional check to ensure it's not part of a larger word
                    # Only for patterns that contain only word characters
                    if re.match(r"^[\w\s]+$", pattern):
                        # Use word boundary check for word-only patterns
                        if re.search(
                            rf"\b{re.escape(pattern)}\b",
                            content,
                            0 if self.config.case_sensitive else re.IGNORECASE,
                        ):
                            return True
                    else:
                        # For patterns with special characters, direct containment is enough
                        if self.config.case_sensitive:
                            if pattern in content:
                                return True
                        else:
                            if pattern.lower() in content.lower():
                                return True
        else:
            # Use compiled patterns for non-exact match
            for pattern in self._compiled_patterns:
                if pattern.search(content):
                    return True

        return False

    def _find_last_coderabbit_comment(
        self, comments: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find the last comment from CodeRabbit in a thread.

        Args:
            comments: List of comments in chronological order

        Returns:
            Last CodeRabbit comment or None if not found
        """
        # Search from end to find most recent CodeRabbit comment
        for comment in reversed(comments):
            if self._is_coderabbit_comment(comment):
                return comment

        return None

    def _is_coderabbit_comment(self, comment: Dict[str, Any]) -> bool:
        """Check if comment is from CodeRabbit.

        Args:
            comment: Comment object to check

        Returns:
            True if comment is from CodeRabbit
        """
        if isinstance(comment, dict):
            # Check user/author information
            user = comment.get("user", {})
            if isinstance(user, dict):
                login = user.get("login", "")
                if "coderabbitai" in login.lower():
                    return True

            # Check author field
            author = comment.get("author", "")
            if "coderabbitai" in str(author).lower():
                return True

            # Check node_id pattern (CodeRabbit specific)
            node_id = comment.get("node_id", "")
            if "coderabbitai" in str(node_id).lower():
                return True

        return False


class ResolvedMarkerManager:
    """High-level manager for resolved marker operations."""

    def __init__(self, config: Optional[ResolvedMarkerConfig] = None):
        """Initialize manager with configuration.

        Args:
            config: Optional configuration for marker detection
        """
        self.config = config or ResolvedMarkerConfig()
        self.detector = ResolvedMarkerDetector(self.config)

    def process_comments_with_resolution(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process comments and apply resolution filtering.

        Args:
            comments: Raw comments from GitHub API

        Returns:
            Dictionary with processed comments and statistics
        """
        # Filter out resolved comments
        unresolved_comments = self.detector.filter_resolved_comments(comments)

        # Get statistics
        stats = self.detector.get_resolution_statistics(comments)

        return {
            "original_comments": comments,
            "unresolved_comments": unresolved_comments,
            "statistics": stats,
            "marker_config": {
                "default_marker": self.config.default_marker,
                "additional_patterns": self.config.additional_patterns,
                "case_sensitive": self.config.case_sensitive,
                "exact_match": self.config.exact_match,
            },
        }

    def process_threads_with_resolution(self, threads: List[ThreadContext]) -> Dict[str, Any]:
        """Process thread contexts and apply resolution filtering.

        Args:
            threads: List of thread contexts

        Returns:
            Dictionary with processed threads and statistics
        """
        # Update resolution status for all threads
        updated_threads = []
        for thread in threads:
            # Create copy with updated resolution status
            status = self.detector.detect_resolution_status(thread)
            # Update the thread's resolution status
            thread.resolution_status = status
            updated_threads.append(thread)

        # Filter out resolved threads
        unresolved_threads = self.detector.filter_resolved_threads(updated_threads)

        resolved_count = len(updated_threads) - len(unresolved_threads)

        return {
            "original_threads": updated_threads,
            "unresolved_threads": unresolved_threads,
            "statistics": {
                "total_threads": len(updated_threads),
                "resolved_threads": resolved_count,
                "unresolved_threads": len(unresolved_threads),
                "resolution_rate": (
                    resolved_count / len(updated_threads) if updated_threads else 0.0
                ),
            },
        }

    def update_config(self, **kwargs) -> None:
        """Update configuration parameters.

        Args:
            **kwargs: Configuration parameters to update
        """
        # Update config object
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Recreate detector with new config
        self.detector = ResolvedMarkerDetector(self.config)

    def add_custom_marker(self, marker: str) -> None:
        """Add a custom resolved marker pattern.

        Args:
            marker: Custom marker string to add
        """
        if marker not in self.config.additional_patterns:
            self.config.additional_patterns.append(marker)
            # Recreate detector to include new pattern
            self.detector = ResolvedMarkerDetector(self.config)

    def validate_marker(self, marker: str) -> Dict[str, Any]:
        """Validate a marker string for security and effectiveness.

        Args:
            marker: Marker string to validate

        Returns:
            Dictionary with validation results and recommendations
        """
        issues = []
        recommendations = []

        # Check length
        if len(marker) < 5:
            issues.append("Marker too short - high risk of false positives")
            recommendations.append("Use at least 5 characters")

        # Check for special characters (good for uniqueness)
        has_special = bool(re.search(r"[^\w\s]", marker))
        if not has_special:
            recommendations.append(
                "Consider adding special characters (emoji, symbols) for uniqueness"
            )

        # Check for common words that might appear in regular text
        common_words = ["the", "and", "or", "but", "for", "is", "was", "are", "were"]
        if any(word.lower() in marker.lower() for word in common_words):
            issues.append("Contains common words - may cause false positives")

        # Check for CodeRabbit specific terms
        if "coderabbit" not in marker.lower() and "cr" not in marker.lower():
            recommendations.append("Consider including 'CodeRabbit' or 'CR' for clarity")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "uniqueness_score": self._calculate_uniqueness_score(marker),
        }

    def _calculate_uniqueness_score(self, marker: str) -> float:
        """Calculate uniqueness score for a marker (0.0 to 1.0).

        Args:
            marker: Marker string to score

        Returns:
            Uniqueness score between 0.0 and 1.0
        """
        score = 0.0

        # Length factor (longer is better up to a point)
        length_score = min(len(marker) / 20.0, 1.0)
        score += length_score * 0.3

        # Special character factor
        special_chars = len(re.findall(r"[^\w\s]", marker))
        special_score = min(special_chars / 5.0, 1.0)
        score += special_score * 0.4

        # Uniqueness factor (uncommon character combinations)
        unique_patterns = len(re.findall(r"[A-Z]{2,}|[0-9]{2,}|[^\w\s]{2,}", marker))
        unique_score = min(unique_patterns / 3.0, 1.0)
        score += unique_score * 0.3

        return min(score, 1.0)

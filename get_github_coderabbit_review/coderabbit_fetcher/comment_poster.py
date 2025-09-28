"""Comment posting functionality for CodeRabbit resolution requests."""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urlparse

# "GitHubClient" import will be added in Task 12 when CLI is implemented
# For now, we use typing.TYPE_CHECKING to avoid import errors in tests
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .github_client import GitHubClient
from .exceptions import CodeRabbitFetcherError


class CommentPostingError(CodeRabbitFetcherError):
    """Exception raised when comment posting fails."""
    pass


class InvalidCommentError(CodeRabbitFetcherError):
    """Exception raised when comment content is invalid."""
    pass


class PRUrlValidationError(CodeRabbitFetcherError):
    """Exception raised when PR URL validation fails."""
    pass


@dataclass
class ResolutionRequestConfig:
    """Configuration for resolution request comments.

    Contains settings for generating and posting resolution
    confirmation requests to CodeRabbit.
    """

    # Default resolved marker to request
    resolved_marker: str = "🔒 CODERABBIT_RESOLVED 🔒"

    # Template for resolution request message
    request_template: str = "@coderabbitai Please verify HEAD and add resolved marker {marker} if there are no issues"

    # Additional context to include in requests
    include_context: bool = True

    # Maximum comment length
    max_comment_length: int = 65536  # GitHub's limit

    # Custom message prefix
    custom_prefix: str = ""

    # Custom message suffix
    custom_suffix: str = ""

    def generate_message(self, additional_context: str = "") -> str:
        """Generate resolution request message.

        Args:
            additional_context: Optional additional context to include

        Returns:
            Formatted resolution request message
        """
        # Start with custom prefix
        message_parts = []
        if self.custom_prefix:
            message_parts.append(self.custom_prefix)

        # Add main request message
        main_message = self.request_template.format(marker=self.resolved_marker)
        message_parts.append(main_message)

        # Add context if enabled and provided
        if self.include_context and additional_context:
            message_parts.append(f"\n\nContext: {additional_context}")

        # Add custom suffix
        if self.custom_suffix:
            message_parts.append(self.custom_suffix)

        # Join all parts
        full_message = "\n".join(message_parts)

        # Validate length
        if len(full_message) > self.max_comment_length:
            # Truncate context if message is too long
            if self.include_context and additional_context:
                available_space = (self.max_comment_length -
                                 len(main_message) -
                                 len(self.custom_prefix or "") -
                                 len(self.custom_suffix or "") -
                                 20)  # Buffer for formatting

                if available_space > 50:  # Minimum useful context size
                    truncated_context = additional_context[:available_space-3] + "..."
                    return self.generate_message(truncated_context)
                else:
                    # Remove context entirely
                    return self.generate_message("")
            else:
                raise InvalidCommentError(f"Comment too long: {len(full_message)} > {self.max_comment_length}")

        return full_message

    def validate_marker(self) -> Dict[str, Any]:
        """Validate the resolved marker.

        Returns:
            Dictionary with validation results
        """
        issues = []

        if not self.resolved_marker:
            issues.append("Resolved marker cannot be empty")

        if len(self.resolved_marker) < 3:
            issues.append("Resolved marker should be at least 3 characters")

        if len(self.resolved_marker) > 100:
            issues.append("Resolved marker should not exceed 100 characters")

        # Check for GitHub mention patterns that might cause issues
        if "@" in self.resolved_marker and "github" in self.resolved_marker.lower():
            issues.append("Resolved marker should not contain GitHub mentions")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }


class CommentPoster:
    """Handles posting resolution request comments to GitHub."""

    def __init__(self, github_client: "GitHubClient", config: Optional[ResolutionRequestConfig] = None):
        """Initialize comment poster.

        Args:
            github_client: GitHub client for API operations
            config: Optional configuration for resolution requests
        """
        self.github_client = github_client
        self.config = config or ResolutionRequestConfig()
        self._validate_config()

    def post_resolution_request(self, pr_url: str, additional_context: str = "") -> Dict[str, Any]:
        """Post a resolution request comment to CodeRabbit.

        Args:
            pr_url: GitHub pull request URL
            additional_context: Optional context to include in the request

        Returns:
            Dictionary with posting results and metadata

        Raises:
            CommentPostingError: If posting fails
            PRUrlValidationError: If PR URL is invalid
        """
        # Validate inputs
        self._validate_pr_url(pr_url)

        # Generate comment message
        try:
            comment_message = self.config.generate_message(additional_context)
        except InvalidCommentError as e:
            raise CommentPostingError("Failed to generate comment") from e

        # Validate comment content
        self._validate_comment_content(comment_message)

        # Post comment
        try:
            result = self.github_client.post_comment(pr_url, comment_message)

            return {
                "success": True,
                "comment_id": result.get("id"),
                "comment_url": result.get("html_url"),
                "message": comment_message,
                "pr_url": pr_url,
                "context_included": (
                    self.config.include_context
                    and bool(additional_context)
                    and "Context:" in comment_message
                ),
                "message_length": len(comment_message),
                "posted_at": result.get("created_at")
            }

        except Exception as e:
            raise CommentPostingError("Failed to post comment") from e

    def generate_resolution_request(self, additional_context: str = "") -> str:
        """Generate a resolution request message without posting.

        Args:
            additional_context: Optional context to include

        Returns:
            Generated resolution request message

        Raises:
            InvalidCommentError: If message generation fails
        """
        return self.config.generate_message(additional_context)

    def batch_post_resolution_requests(self, pr_urls: List[str],
                                     context_per_url: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Post resolution requests to multiple pull requests.

        Args:
            pr_urls: List of GitHub pull request URLs
            context_per_url: Optional mapping of URL to specific context

        Returns:
            Dictionary with batch posting results
        """
        results = {
            "successful_posts": [],
            "failed_posts": [],
            "total_urls": len(pr_urls),
            "success_count": 0,
            "failure_count": 0
        }

        for pr_url in pr_urls:
            try:
                context = context_per_url.get(pr_url, "") if context_per_url else ""
                result = self.post_resolution_request(pr_url, context)
                results["successful_posts"].append(result)
                results["success_count"] += 1

            except (CommentPostingError, PRUrlValidationError) as e:
                failed_result = {
                    "pr_url": pr_url,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                results["failed_posts"].append(failed_result)
                results["failure_count"] += 1

        results["success_rate"] = results["success_count"] / results["total_urls"] if results["total_urls"] > 0 else 0.0

        return results

    def validate_resolution_request(self, additional_context: str = "") -> Dict[str, Any]:
        """Validate a resolution request without posting.

        Args:
            additional_context: Context to validate with the request

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "message_preview": "",
            "message_length": 0
        }

        # Validate configuration
        config_validation = self.config.validate_marker()
        if not config_validation["valid"]:
            validation_result["valid"] = False
            validation_result["issues"].extend(config_validation["issues"])

        # Try to generate message
        try:
            message = self.config.generate_message(additional_context)
            validation_result["message_preview"] = message[:200] + "..." if len(message) > 200 else message
            validation_result["message_length"] = len(message)

            # Check message content
            content_issues = self._validate_comment_content(message, raise_on_error=False)
            if content_issues:
                validation_result["issues"].extend(content_issues)
                validation_result["valid"] = False

        except InvalidCommentError as e:
            validation_result["valid"] = False
            validation_result["issues"].append(str(e))

        # Add warnings for potential issues
        if additional_context and len(additional_context) > 1000:
            validation_result["warnings"].append("Additional context is quite long and may be truncated")

        if self.config.resolved_marker and len(self.config.resolved_marker) > 50:
            validation_result["warnings"].append("Resolved marker is quite long")

        return validation_result

    def update_config(self, **kwargs) -> None:
        """Update configuration parameters.

        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")

        self._validate_config()

    def get_posting_statistics(self) -> Dict[str, Any]:
        """Get statistics about comment posting capabilities.

        Returns:
            Dictionary with posting statistics and limits
        """
        return {
            "max_comment_length": self.config.max_comment_length,
            "resolved_marker": self.config.resolved_marker,
            "marker_length": len(self.config.resolved_marker),
            "template_length": len(self.config.request_template),
            "github_client_authenticated": self.github_client.is_authenticated(),
            "config_valid": self.config.validate_marker()["valid"]
        }

    def _validate_config(self) -> None:
        """Validate the current configuration.

        Raises:
            InvalidCommentError: If configuration is invalid
        """
        marker_validation = self.config.validate_marker()
        if not marker_validation["valid"]:
            issues = "; ".join(marker_validation["issues"])
            raise InvalidCommentError(f"Invalid configuration: {issues}")

    def _validate_pr_url(self, pr_url: str) -> None:
        """Validate GitHub pull request URL.

        Args:
            pr_url: URL to validate

        Raises:
            PRUrlValidationError: If URL is invalid
        """
        if not pr_url:
            raise PRUrlValidationError("PR URL cannot be empty")

        # Parse URL
        try:
            parsed = urlparse(pr_url)
        except Exception as e:
            raise PRUrlValidationError("Invalid URL format") from e

        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            raise PRUrlValidationError("URL must use HTTP or HTTPS")

        # Check domain
        if not parsed.netloc:
            raise PRUrlValidationError("URL must have a valid domain")

        # Check if it's GitHub domain
        netloc_lower = parsed.netloc.lower()
        if not (netloc_lower == "github.com" or netloc_lower == "www.github.com"):
            raise PRUrlValidationError("URL must be a GitHub.com URL")

        # Check path structure
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) < 4 or path_parts[2] != "pull":
            raise PRUrlValidationError("URL must be a GitHub pull request URL (e.g., https://github.com/owner/repo/pull/123)")

        # Check PR number
        try:
            pr_number = int(path_parts[3])
            if pr_number <= 0:
                raise ValueError("PR number must be positive")
        except ValueError:
            raise PRUrlValidationError("Invalid pull request number")

    def _validate_comment_content(self, content: str, raise_on_error: bool = True) -> List[str]:
        """Validate comment content.

        Args:
            content: Comment content to validate
            raise_on_error: Whether to raise exception on validation failure

        Returns:
            List of validation issues (empty if valid)

        Raises:
            InvalidCommentError: If content is invalid and raise_on_error is True
        """
        issues = []

        if not content or not content.strip():
            issues.append("Comment content cannot be empty")

        if len(content) > self.config.max_comment_length:
            issues.append(f"Comment too long: {len(content)} > {self.config.max_comment_length}")

        # Check for potentially problematic content
        if "@everyone" in content or "@here" in content:
            issues.append("Comment should not contain @everyone or @here mentions")

        # Check for balanced markdown
        if content.count("```") % 2 != 0:
            issues.append("Unbalanced code block markers (```)")

        # Check for excessive newlines
        if "\n\n\n\n" in content:
            issues.append("Comment contains excessive blank lines")

        if raise_on_error and issues:
            raise InvalidCommentError("; ".join(issues))

        return issues

    def extract_pr_info(self, pr_url: str) -> Dict[str, str]:
        """Extract owner, repo, and PR number from URL.

        Args:
            pr_url: GitHub pull request URL

        Returns:
            Dictionary with owner, repo, and pr_number

        Raises:
            PRUrlValidationError: If URL is invalid
        """
        self._validate_pr_url(pr_url)

        parsed = urlparse(pr_url)
        path_parts = [p for p in parsed.path.split("/") if p]

        return {
            "owner": path_parts[0],
            "repo": path_parts[1],
            "pr_number": path_parts[3]
        }


class ResolutionRequestManager:
    """High-level manager for resolution request operations."""

    def __init__(self, github_client: "GitHubClient", config: Optional[ResolutionRequestConfig] = None):
        """Initialize resolution request manager.

        Args:
            github_client: GitHub client for API operations
            config: Optional configuration for resolution requests
        """
        self.poster = CommentPoster(github_client, config)
        self.github_client = github_client

    def request_resolution_for_comments(self, pr_url: str, comment_ids: List[Union[str, int]],
                                      include_summary: bool = True) -> Dict[str, Any]:
        """Request resolution for specific comments in a pull request.

        Args:
            pr_url: GitHub pull request URL
            comment_ids: List of comment IDs (strings or integers) to request resolution for
            include_summary: Whether to include a summary of comment IDs

        Returns:
            Dictionary with request results
        """
        if include_summary and comment_ids:
            ids_str = ", ".join(map(str, comment_ids[:10]))
            context = f"Requesting resolution verification for comments: {ids_str}"
            if len(comment_ids) > 10:
                context += f" and {len(comment_ids) - 10} more comments"
        else:
            context = ""

        return self.poster.post_resolution_request(pr_url, context)

    def request_resolution_with_summary(self, pr_url: str, summary: str) -> Dict[str, Any]:
        """Request resolution with a custom summary.

        Args:
            pr_url: GitHub pull request URL
            summary: Summary of changes or context

        Returns:
            Dictionary with request results
        """
        context = f"Summary of changes: {summary}"
        return self.poster.post_resolution_request(pr_url, context)

    def validate_and_post(self, pr_url: str, additional_context: str = "") -> Dict[str, Any]:
        """Validate configuration and post resolution request.

        Args:
            pr_url: GitHub pull request URL
            additional_context: Optional context to include

        Returns:
            Dictionary with validation and posting results
        """
        # First validate
        validation = self.poster.validate_resolution_request(additional_context)

        if not validation["valid"]:
            return {
                "success": False,
                "validation": validation,
                "error": "Validation failed: " + "; ".join(validation["issues"])
            }

        # Post if validation passes
        try:
            posting_result = self.poster.post_resolution_request(pr_url, additional_context)
            return {
                "success": True,
                "validation": validation,
                "posting": posting_result
            }
        except CommentPostingError as e:
            return {
                "success": False,
                "validation": validation,
                "error": str(e)
            }

    def get_config_template(self) -> Dict[str, Any]:
        """Get a template for configuration customization.

        Returns:
            Dictionary with configuration template and examples
        """
        return {
            "resolved_marker": {
                "default": "🔒 CODERABBIT_RESOLVED 🔒",
                "examples": [
                    "✅ VERIFIED_AND_RESOLVED ✅",
                    "🔐 CR_RESOLUTION_CONFIRMED 🔐",
                    "[RESOLVED_BY_CODERABBIT]"
                ],
                "recommendations": [
                    "Use special characters or emoji for uniqueness",
                    "Keep it concise but descriptive",
                    "Avoid common words that might appear in regular text"
                ]
            },
            "request_template": {
                "default": "@coderabbitai Please verify HEAD and add resolved marker {marker} if there are no issues",
                "examples": [
                    "@coderabbitai Please review the latest changes and mark as {marker} if resolved",
                    "@coderabbitai Could you verify the fix and add {marker} if everything looks good?",
                    "@coderabbitai Please check HEAD and add {marker} when verified"
                ]
            },
            "custom_options": {
                "custom_prefix": "Optional text to add before the main request",
                "custom_suffix": "Optional text to add after the main request",
                "include_context": "Whether to include additional context in requests",
                "max_comment_length": "Maximum allowed comment length (GitHub limit: 65536)"
            }
        }

    def update_poster_config(self, **kwargs) -> None:
        """Update poster configuration.

        Args:
            **kwargs: Configuration parameters to update
        """
        self.poster.update_config(**kwargs)

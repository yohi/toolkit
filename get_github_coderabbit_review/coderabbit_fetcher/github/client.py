"""
GitHub CLI wrapper for authenticated API access.

This module provides a wrapper around the GitHub CLI (gh) for secure
API access with proper authentication and error handling.
"""

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import urlparse

from rich.console import Console

from ..exceptions import (
    GitHubAuthenticationError,
    InvalidPRUrlError,
    APIRateLimitError,
    CodeRabbitFetcherError,
)

console = Console()


class GitHubClient:
    """GitHub CLI wrapper for authenticated API access.

    Provides methods for fetching pull request data, posting comments,
    and managing authentication through the GitHub CLI.
    """

    def __init__(
        self, 
        max_retries: int = 3, 
        retry_delay: float = 1.0,
        check_gh_cli: bool = True
    ) -> None:
        """Initialize GitHub client.

        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Base delay between retries in seconds
            check_gh_cli: Whether to check GitHub CLI availability on initialization
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        if check_gh_cli:
            self._check_gh_cli_availability()

    def _check_gh_cli_availability(self) -> None:
        """Check if GitHub CLI is available on the system.

        Raises:
            CodeRabbitFetcherError: If GitHub CLI is not found
        """
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise CodeRabbitFetcherError(
                    "GitHub CLI is not properly installed",
                    details="Install GitHub CLI from https://cli.github.com/"
                )
        except FileNotFoundError:
            raise CodeRabbitFetcherError(
                "GitHub CLI (gh) not found in PATH",
                details="Install GitHub CLI from https://cli.github.com/"
            )
        except subprocess.TimeoutExpired:
            raise CodeRabbitFetcherError("GitHub CLI command timed out")

    def check_authentication(self) -> bool:
        """Verify GitHub CLI authentication status.

        Returns:
            True if authenticated, False otherwise

        Raises:
            GitHubAuthenticationError: If authentication check fails
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # gh auth status returns 0 when authenticated
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            raise GitHubAuthenticationError("Authentication check timed out")
        except Exception as e:
            raise GitHubAuthenticationError(f"Authentication check failed: {e}")

    def parse_pr_url(self, pr_url: str) -> Tuple[str, str, int]:
        """Parse GitHub pull request URL.

        Args:
            pr_url: GitHub pull request URL

        Returns:
            Tuple of (owner, repo, pr_number)

        Raises:
            InvalidPRUrlError: If URL format is invalid
        """
        # Support multiple URL formats
        patterns = [
            r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$",
            r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/.*$",
        ]

        url = pr_url.strip()

        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                owner, repo, pr_number_str = match.groups()
                return owner, repo, int(pr_number_str)

        raise InvalidPRUrlError(f"Invalid GitHub pull request URL: {pr_url}")

    def _execute_gh_command(self, args: list[str], timeout: int = 30) -> Dict[str, Any]:
        """Execute GitHub CLI command with retry logic.

        Args:
            args: Command arguments for gh CLI
            timeout: Command timeout in seconds

        Returns:
            Parsed JSON response from gh CLI

        Raises:
            APIRateLimitError: If rate limit is exceeded
            CodeRabbitFetcherError: For other command failures
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                console.print(f"🔄 [dim]Executing: gh {' '.join(args)}[/dim]", highlight=False)

                result = subprocess.run(
                    ["gh"] + args,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                if result.returncode == 0:
                    try:
                        return json.loads(result.stdout)
                    except json.JSONDecodeError as e:
                        raise CodeRabbitFetcherError(
                            f"Invalid JSON response from GitHub CLI: {e}",
                            details=f"Output: {result.stdout[:500]}"
                        )

                # Handle specific error cases
                stderr_lower = result.stderr.lower()

                if "rate limit" in stderr_lower:
                    # Extract rate limit reset time if available
                    reset_time = self._extract_rate_limit_reset(result.stderr)
                    raise APIRateLimitError(reset_time=reset_time)

                if "not found" in stderr_lower or "404" in stderr_lower:
                    raise CodeRabbitFetcherError(
                        "Pull request not found or access denied",
                        details=result.stderr
                    )

                if "authentication" in stderr_lower or "unauthorized" in stderr_lower:
                    raise GitHubAuthenticationError(
                        "GitHub CLI authentication required or expired"
                    )

                # For other errors, retry if we have attempts left
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    console.print(f"⏳ [yellow]Command failed, retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})[/yellow]")
                    time.sleep(wait_time)
                    continue

                # Final attempt failed
                raise CodeRabbitFetcherError(
                    f"GitHub CLI command failed: {result.stderr}",
                    details=f"Return code: {result.returncode}\nStdout: {result.stdout}"
                )

            except subprocess.TimeoutExpired:
                last_exception = CodeRabbitFetcherError(
                    f"GitHub CLI command timed out after {timeout} seconds"
                )
                if attempt < self.max_retries:
                    console.print(f"⏳ [yellow]Command timed out, retrying... (attempt {attempt + 1}/{self.max_retries})[/yellow]")
                    continue
            except (APIRateLimitError, GitHubAuthenticationError):
                # Don't retry these specific errors
                raise
            except Exception as e:
                last_exception = CodeRabbitFetcherError(f"Unexpected error: {e}")
                if attempt < self.max_retries:
                    console.print(f"⏳ [yellow]Unexpected error, retrying... (attempt {attempt + 1}/{self.max_retries})[/yellow]")
                    continue

        # All retries exhausted
        if last_exception:
            raise last_exception

        raise CodeRabbitFetcherError("All retry attempts failed")

    def _extract_rate_limit_reset(self, stderr: str) -> int | None:
        """Extract rate limit reset time from error message.

        Args:
            stderr: Error message from GitHub CLI

        Returns:
            Unix timestamp when rate limit resets, or None if not found
        """
        # Look for patterns like "resets at 2023-12-01T12:00:00Z"
        import re
        from datetime import datetime

        patterns = [
            r"resets at (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)",
            r"reset time: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, stderr)
            if match:
                try:
                    dt = datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))
                    return int(dt.timestamp())
                except ValueError:
                    continue

        return None

    def fetch_pr_comments(self, pr_url: str) -> Dict[str, Any]:
        """Fetch pull request comments using GitHub CLI.

        Args:
            pr_url: GitHub pull request URL

        Returns:
            Complete pull request data including comments

        Raises:
            InvalidPRUrlError: If URL format is invalid
            GitHubAuthenticationError: If not authenticated
            APIRateLimitError: If rate limit exceeded
            CodeRabbitFetcherError: For other failures
        """
        owner, repo, pr_number = self.parse_pr_url(pr_url)

        console.print(f"📥 [blue]Fetching PR data for {owner}/{repo}#{pr_number}[/blue]")

        # Fetch PR data with comments and reviews
        pr_data = self._execute_gh_command([
            "pr", "view", str(pr_number),
            "--repo", f"{owner}/{repo}",
            "--json", "number,title,body,comments,reviews,state,author,createdAt,updatedAt"
        ])

        # Fetch additional comment details (reviews contain inline comments)
        try:
            review_comments = self._execute_gh_command([
                "api", f"repos/{owner}/{repo}/pulls/{pr_number}/comments?per_page=100"
            ])

            # Merge review comments into the main data structure
            if isinstance(review_comments, list):
                pr_data["reviewComments"] = review_comments

        except Exception as e:
            console.print(f"⚠️ [yellow]Could not fetch review comments: {e}[/yellow]")
            pr_data["reviewComments"] = []

        console.print(f"✅ [green]Fetched {len(pr_data.get('comments', []))} comments and {len(pr_data.get('reviewComments', []))} review comments[/green]")

        return pr_data

    def post_comment(self, pr_url: str, comment: str) -> bool:
        """Post a comment to a pull request.

        Args:
            pr_url: GitHub pull request URL
            comment: Comment text to post

        Returns:
            True if comment was posted successfully

        Raises:
            InvalidPRUrlError: If URL format is invalid
            GitHubAuthenticationError: If not authenticated
            CodeRabbitFetcherError: For other failures
        """
        owner, repo, pr_number = self.parse_pr_url(pr_url)

        console.print(f"📤 [blue]Posting comment to {owner}/{repo}#{pr_number}[/blue]")

        try:
            # PRはIssueとしてコメントAPIが利用可能
            self._execute_gh_command([
                "api", f"repos/{owner}/{repo}/issues/{pr_number}/comments",
                "--method", "POST",
                "-f", f"body={comment}",
            ])

            console.print("✅ [green]Comment posted successfully[/green]")
            return True

        except Exception as e:
            console.print(f"❌ [red]Failed to post comment: {e}[/red]")
            return False

    def get_authenticated_user(self) -> str:
        """Get the username of the authenticated user.

        Returns:
            GitHub username

        Raises:
            GitHubAuthenticationError: If not authenticated
        """
        try:
            result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()

            raise GitHubAuthenticationError("Could not get authenticated user")

        except subprocess.TimeoutExpired:
            raise GitHubAuthenticationError("Authentication check timed out")
        except Exception as e:
            raise GitHubAuthenticationError(f"Authentication check failed: {e}")

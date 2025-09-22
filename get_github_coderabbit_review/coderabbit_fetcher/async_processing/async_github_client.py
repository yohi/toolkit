"""Async GitHub client for CodeRabbit fetcher."""

import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional

import aiohttp

from ..exceptions import APIRateLimitError, GitHubAuthenticationError, InvalidPRUrlError

logger = logging.getLogger(__name__)


class AsyncGitHubClient:
    """Async GitHub API client."""

    def __init__(self, token: Optional[str] = None, timeout: int = 30):
        """Initialize async GitHub client.

        Args:
            token: GitHub personal access token
            timeout: Request timeout in seconds
        """
        self.token = token
        self.timeout = timeout
        self.base_url = "https://api.github.com"

        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._active_requests: set = set()

        # Rate limiting
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeRabbit-Fetcher/1.0",
            }

            if self.token:
                headers["Authorization"] = f"token {self.token}"

            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(
                    limit=100,  # Total connection pool size
                    limit_per_host=30,  # Connections per host
                    ttl_dns_cache=300,  # DNS cache TTL
                    use_dns_cache=True,
                ),
            )

    async def close(self) -> None:
        """Close the HTTP session and cancel active requests."""
        # Cancel active requests
        if self._active_requests:
            for request in list(self._active_requests):
                if not request.done():
                    request.cancel()

        # Close session
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def cancel_operations(self) -> None:
        """Cancel all ongoing operations."""
        await self.close()

    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make async HTTP request to GitHub API.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            Response data

        Raises:
            GitHubAuthenticationError: If authentication fails
            aiohttp.ClientError: For other HTTP errors
        """
        await self._ensure_session()

        # Track current task for cancellation
        current_task = asyncio.current_task()
        if current_task:
            self._active_requests.add(current_task)

        try:
            async with self._session.request(method, url, **kwargs) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                self.rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", 0))

                # Check for rate limiting
                if response.status == 403 and "rate limit" in (await response.text()).lower():
                    logger.warning("GitHub API rate limit exceeded")
                    # Calculate wait time until rate limit resets
                    wait_time = max(0, self.rate_limit_reset - time.time())
                    if wait_time > 0 and wait_time < 3600:  # Wait up to 1 hour
                        logger.info(f"Waiting {wait_time:.0f} seconds for rate limit reset")
                        await asyncio.sleep(wait_time)
                        # Retry the request
                        return await self._make_request(method, url, **kwargs)
                    raise APIRateLimitError(
                        f"Rate limit exceeded. Reset at {self.rate_limit_reset}"
                    )

                # Handle authentication errors
                if response.status == 401:
                    raise GitHubAuthenticationError("GitHub authentication failed")

                # Handle other errors
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"GitHub API error {response.status}: {error_text}")
                    response.raise_for_status()

                # Parse JSON response
                if response.content_type == "application/json":
                    return await response.json()
                else:
                    return {"content": await response.text()}

        except asyncio.CancelledError:
            logger.info("GitHub request was cancelled")
            raise
        except Exception:
            logger.exception("Error making GitHub request")
            raise
        finally:
            if current_task:
                self._active_requests.discard(current_task)

    async def validate_auth_async(self) -> bool:
        """Validate GitHub authentication asynchronously.

        Returns:
            True if authentication is valid
        """
        try:
            url = f"{self.base_url}/user"
            await self._make_request("GET", url)
            return True
        except Exception as e:
            logger.error(f"GitHub authentication validation failed: {e}")
            return False

    async def extract_pr_info_async(self, pr_url: str) -> Dict[str, Any]:
        """Extract PR information from URL asynchronously.

        Args:
            pr_url: GitHub PR URL

        Returns:
            PR information

        Raises:
            InvalidPRUrlError: If URL is invalid
        """
        # Parse GitHub PR URL
        pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.match(pattern, pr_url)

        if not match:
            raise InvalidPRUrlError(f"Invalid GitHub PR URL: {pr_url}")

        owner, repo, pr_number = match.groups()

        # Fetch PR information
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        pr_data = await self._make_request("GET", url)

        return {
            "owner": owner,
            "repo": repo,
            "number": int(pr_number),
            "title": pr_data.get("title", ""),
            "body": pr_data.get("body", ""),
            "state": pr_data.get("state", ""),
            "created_at": pr_data.get("created_at", ""),
            "updated_at": pr_data.get("updated_at", ""),
            "url": pr_url,
        }

    async def get_pr_comments_async(
        self, owner: str, repo: str, pr_number: int, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get PR comments asynchronously.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            per_page: Items per page

        Returns:
            List of comments
        """
        comments = []
        page = 1

        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
            params = {"page": page, "per_page": per_page}

            try:
                page_comments = await self._make_request("GET", url, params=params)

                if not page_comments:
                    break

                comments.extend(page_comments)

                # Check if we got a full page (more pages likely exist)
                if len(page_comments) < per_page:
                    break

                page += 1

                # Safety limit
                if page > 50:  # Max 5000 comments
                    logger.warning("Reached maximum page limit for comments")
                    break

            except Exception as e:
                logger.error(f"Error fetching comments page {page}: {e}")
                break

        logger.info(f"Fetched {len(comments)} comments from PR #{pr_number}")
        return comments

    async def get_pr_reviews_async(
        self, owner: str, repo: str, pr_number: int, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get PR reviews asynchronously.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            per_page: Items per page

        Returns:
            List of reviews
        """
        reviews = []
        page = 1

        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            params = {"page": page, "per_page": per_page}

            try:
                page_reviews = await self._make_request("GET", url, params=params)

                if not page_reviews:
                    break

                reviews.extend(page_reviews)

                if len(page_reviews) < per_page:
                    break

                page += 1

                # Safety limit
                if page > 20:  # Max 2000 reviews
                    logger.warning("Reached maximum page limit for reviews")
                    break

            except Exception as e:
                logger.error(f"Error fetching reviews page {page}: {e}")
                break

        logger.info(f"Fetched {len(reviews)} reviews from PR #{pr_number}")
        return reviews

    async def get_pr_files_async(
        self, owner: str, repo: str, pr_number: int, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get PR files asynchronously.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            per_page: Items per page

        Returns:
            List of files
        """
        files = []
        page = 1

        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            params = {"page": page, "per_page": per_page}

            try:
                page_files = await self._make_request("GET", url, params=params)

                if not page_files:
                    break

                files.extend(page_files)

                if len(page_files) < per_page:
                    break

                page += 1

                # Safety limit for large PRs
                if page > 50:  # Max 5000 files
                    logger.warning("Reached maximum page limit for files")
                    break

            except Exception as e:
                logger.error(f"Error fetching files page {page}: {e}")
                break

        logger.info(f"Fetched {len(files)} files from PR #{pr_number}")
        return files

    async def get_pr_commits_async(
        self, owner: str, repo: str, pr_number: int, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get PR commits asynchronously.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            per_page: Items per page

        Returns:
            List of commits
        """
        commits = []
        page = 1

        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
            params = {"page": page, "per_page": per_page}

            try:
                page_commits = await self._make_request("GET", url, params=params)

                if not page_commits:
                    break

                commits.extend(page_commits)

                if len(page_commits) < per_page:
                    break

                page += 1

                # Safety limit
                if page > 20:  # Max 2000 commits
                    logger.warning("Reached maximum page limit for commits")
                    break

            except Exception as e:
                logger.error(f"Error fetching commits page {page}: {e}")
                break

        logger.info(f"Fetched {len(commits)} commits from PR #{pr_number}")
        return commits

    async def get_pr_review_comments_async(
        self, owner: str, repo: str, pr_number: int, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get PR review comments asynchronously.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            per_page: Items per page

        Returns:
            List of review comments
        """
        comments = []
        page = 1

        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
            params = {"page": page, "per_page": per_page}

            try:
                page_comments = await self._make_request("GET", url, params=params)

                if not page_comments:
                    break

                comments.extend(page_comments)

                if len(page_comments) < per_page:
                    break

                page += 1

                # Safety limit
                if page > 50:  # Max 5000 comments
                    logger.warning("Reached maximum page limit for review comments")
                    break

            except Exception as e:
                logger.error(f"Error fetching review comments page {page}: {e}")
                break

        logger.info(f"Fetched {len(comments)} review comments from PR #{pr_number}")
        return comments

    async def fetch_all_pr_data_async(
        self, owner: str, repo: str, pr_number: int
    ) -> Dict[str, Any]:
        """Fetch all PR data concurrently.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            Dictionary with all PR data
        """
        logger.info(f"Fetching all data for PR #{pr_number} concurrently...")

        # Create concurrent tasks
        tasks = [
            asyncio.create_task(
                self.get_pr_comments_async(owner, repo, pr_number), name="comments"
            ),
            asyncio.create_task(self.get_pr_reviews_async(owner, repo, pr_number), name="reviews"),
            asyncio.create_task(self.get_pr_files_async(owner, repo, pr_number), name="files"),
            asyncio.create_task(self.get_pr_commits_async(owner, repo, pr_number), name="commits"),
            asyncio.create_task(
                self.get_pr_review_comments_async(owner, repo, pr_number), name="review_comments"
            ),
        ]

        # Execute all tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            data = {}
            task_names = ["comments", "reviews", "files", "commits", "review_comments"]

            for i, result in enumerate(results):
                task_name = task_names[i]
                if isinstance(result, Exception):
                    logger.error(f"Failed to fetch {task_name}: {result}")
                    data[task_name] = []
                else:
                    data[task_name] = result

            logger.info("Successfully fetched all PR data")
            return data

        except Exception as e:
            logger.error(f"Error fetching PR data: {e}")
            raise

    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information.

        Returns:
            Rate limit information
        """
        return {
            "remaining": self.rate_limit_remaining,
            "reset_timestamp": self.rate_limit_reset,
            "estimated_requests_per_hour": min(5000, self.rate_limit_remaining * 2),
        }

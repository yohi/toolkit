"""
Unit tests for GitHub client functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess

from coderabbit_fetcher.github.client import GitHubClient
from coderabbit_fetcher.github.comment_poster import CommentPoster
from coderabbit_fetcher.exceptions import (
    GitHubAuthenticationError,
    InvalidPRUrlError,
    APIRateLimitError,
    CodeRabbitFetcherError,
)


class TestGitHubClient:
    """Test GitHubClient functionality."""

    def test_parse_pr_url_valid(self):
        """Test parsing valid PR URLs."""
        client = GitHubClient(check_gh_cli=False)

        test_cases = [
            ("https://github.com/owner/repo/pull/123", ("owner", "repo", 123)),
            ("https://github.com/owner/repo/pull/456/", ("owner", "repo", 456)),
            ("https://github.com/owner/repo/pull/789/files", ("owner", "repo", 789)),
        ]

        for url, expected in test_cases:
            owner, repo, pr_number = client.parse_pr_url(url)
            assert (owner, repo, pr_number) == expected

    def test_parse_pr_url_invalid(self):
        """Test parsing invalid PR URLs."""
        client = GitHubClient(check_gh_cli=False)

        invalid_urls = [
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/issues/123",
            "https://gitlab.com/owner/repo/pull/123",
            "not-a-url",
            "",
        ]

        for url in invalid_urls:
            with pytest.raises(InvalidPRUrlError):
                client.parse_pr_url(url)

    @patch('subprocess.run')
    def test_check_authentication_success(self, mock_run):
        """Test successful authentication check."""
        mock_run.return_value = Mock(returncode=0)

        client = GitHubClient(check_gh_cli=False)
        assert client.check_authentication() is True

    @patch('subprocess.run')
    def test_check_authentication_failure(self, mock_run):
        """Test failed authentication check."""
        mock_run.return_value = Mock(returncode=1)

        client = GitHubClient(check_gh_cli=False)
        assert client.check_authentication() is False

    @patch('subprocess.run')
    def test_check_authentication_timeout(self, mock_run):
        """Test authentication check timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(['gh', 'auth', 'status'], 10)

        client = GitHubClient(check_gh_cli=False)
        with pytest.raises(GitHubAuthenticationError):
            client.check_authentication()

    @patch('subprocess.run')
    def test_execute_gh_command_success(self, mock_run):
        """Test successful gh command execution."""
        test_data = {"test": "data"}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(test_data),
            stderr=""
        )

        client = GitHubClient(check_gh_cli=False)
        result = client._execute_gh_command(["api", "user"])

        assert result == test_data
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_execute_gh_command_rate_limit(self, mock_run):
        """Test rate limit error handling."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="rate limit exceeded"
        )

        client = GitHubClient(check_gh_cli=False)
        with pytest.raises(APIRateLimitError):
            client._execute_gh_command(["api", "user"])

    @patch('subprocess.run')
    def test_execute_gh_command_not_found(self, mock_run):
        """Test not found error handling."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="not found"
        )

        client = GitHubClient(check_gh_cli=False)
        with pytest.raises(CodeRabbitFetcherError):
            client._execute_gh_command(["api", "nonexistent"])

    @patch('subprocess.run')
    def test_execute_gh_command_authentication_error(self, mock_run):
        """Test authentication error handling."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="authentication required"
        )

        client = GitHubClient(check_gh_cli=False)
        with pytest.raises(GitHubAuthenticationError):
            client._execute_gh_command(["api", "user"])

    @patch('subprocess.run')
    def test_execute_gh_command_invalid_json(self, mock_run):
        """Test invalid JSON response handling."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="invalid json",
            stderr=""
        )

        client = GitHubClient(check_gh_cli=False)
        with pytest.raises(CodeRabbitFetcherError):
            client._execute_gh_command(["api", "user"])

    @patch('subprocess.run')
    def test_execute_gh_command_retry(self, mock_run):
        """Test retry logic for transient failures."""
        # First call fails, second succeeds
        test_data = {"test": "data"}
        mock_run.side_effect = [
            Mock(returncode=1, stdout="", stderr="temporary error"),
            Mock(returncode=0, stdout=json.dumps(test_data), stderr="")
        ]

        client = GitHubClient(max_retries=1, retry_delay=0.1, check_gh_cli=False)
        result = client._execute_gh_command(["api", "user"])

        assert result == test_data
        assert mock_run.call_count == 2

    @patch.object(GitHubClient, '_execute_gh_command')
    def test_fetch_pr_comments(self, mock_execute):
        """Test fetching PR comments."""
        test_pr_data = {
            "number": 123,
            "title": "Test PR",
            "comments": [{"id": 1, "body": "Test comment"}],
            "reviews": [{"id": 2, "body": "Test review"}]
        }

        test_review_comments = [{"id": 3, "body": "Review comment"}]

        mock_execute.side_effect = [test_pr_data, test_review_comments]

        client = GitHubClient(check_gh_cli=False)
        result = client.fetch_pr_comments("https://github.com/owner/repo/pull/123")

        assert result["number"] == 123
        assert result["reviewComments"] == test_review_comments
        assert mock_execute.call_count == 2

    @patch.object(GitHubClient, '_execute_gh_command')
    def test_post_comment(self, mock_execute):
        """Test posting a comment."""
        mock_execute.return_value = {}

        client = GitHubClient(check_gh_cli=False)
        result = client.post_comment("https://github.com/owner/repo/pull/123", "Test comment")

        assert result is True
        mock_execute.assert_called_once()

    @patch.object(GitHubClient, '_execute_gh_command')
    def test_post_comment_failure(self, mock_execute):
        """Test comment posting failure."""
        mock_execute.side_effect = CodeRabbitFetcherError("Posting failed")

        client = GitHubClient(check_gh_cli=False)
        result = client.post_comment("https://github.com/owner/repo/pull/123", "Test comment")

        assert result is False

    @patch('subprocess.run')
    def test_get_authenticated_user(self, mock_run):
        """Test getting authenticated user."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="testuser\n",
            stderr=""
        )

        client = GitHubClient(check_gh_cli=False)
        username = client.get_authenticated_user()

        assert username == "testuser"

    def test_extract_rate_limit_reset(self):
        """Test extracting rate limit reset time."""
        client = GitHubClient(check_gh_cli=False)

        # Test with reset time in stderr
        stderr_with_time = "rate limit exceeded, resets at 2023-12-01T12:00:00Z"
        reset_time = client._extract_rate_limit_reset(stderr_with_time)
        assert reset_time is not None
        assert isinstance(reset_time, int)

        # Test without reset time
        stderr_without_time = "rate limit exceeded"
        reset_time = client._extract_rate_limit_reset(stderr_without_time)
        assert reset_time is None


class TestCommentPoster:
    """Test CommentPoster functionality."""

    def test_generate_resolution_request(self):
        """Test generating resolution request comment."""
        client = Mock()
        poster = CommentPoster(client)

        marker = "🔒 RESOLVED 🔒"
        comment = poster.generate_resolution_request(marker)

        assert "@coderabbitai" in comment
        assert marker in comment
        assert "verify HEAD" in comment

    def test_post_resolution_request_success(self):
        """Test successful resolution request posting."""
        client = Mock()
        client.post_comment.return_value = True

        poster = CommentPoster(client)
        result = poster.post_resolution_request(
            "https://github.com/owner/repo/pull/123",
            "🔒 RESOLVED 🔒"
        )

        assert result is True
        client.post_comment.assert_called_once()

    def test_post_resolution_request_failure(self):
        """Test failed resolution request posting."""
        client = Mock()
        client.post_comment.return_value = False

        poster = CommentPoster(client)
        result = poster.post_resolution_request(
            "https://github.com/owner/repo/pull/123",
            "🔒 RESOLVED 🔒"
        )

        assert result is False

    def test_post_custom_comment(self):
        """Test posting custom comment."""
        client = Mock()
        client.post_comment.return_value = True

        poster = CommentPoster(client)
        result = poster.post_custom_comment(
            "https://github.com/owner/repo/pull/123",
            "Custom comment"
        )

        assert result is True
        client.post_comment.assert_called_with(
            "https://github.com/owner/repo/pull/123",
            "Custom comment"
        )

    def test_validate_comment_permissions(self):
        """Test validating comment permissions."""
        client = Mock()
        client.get_authenticated_user.return_value = "testuser"
        client.parse_pr_url.return_value = ("owner", "repo", 123)

        poster = CommentPoster(client)
        result = poster.validate_comment_permissions(
            "https://github.com/owner/repo/pull/123"
        )

        assert result is True

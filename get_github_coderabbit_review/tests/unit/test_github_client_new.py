"""Tests for the refactored GitHubClient with REST API implementation."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from coderabbit_fetcher.exceptions import InvalidPRUrlError
from coderabbit_fetcher.github_client import GitHubAPIError, GitHubClient


class TestGitHubClientRefactored:
    """Test the refactored GitHubClient with REST API implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(GitHubClient, "check_authentication"):
            self.client = GitHubClient()
        # Mock authentication status
        self.client._authenticated = True

    @patch("subprocess.run")
    def test_post_comment_success(self, mock_run):
        """Test successful comment posting with REST API."""
        # Mock successful API response
        mock_response = {
            "id": 123456789,
            "html_url": "https://github.com/owner/repo/pull/1#issuecomment-123456789",
            "body": "Test comment",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "user": {"login": "testuser"},
            "node_id": "IC_kwDOABCD12345",
        }

        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(mock_response))

        result = self.client.post_comment("https://github.com/owner/repo/pull/1", "Test comment")

        # Verify the API call
        mock_run.assert_called_once()
        call_args = mock_run.call_args

        # Check command structure
        assert call_args[0][0] == [
            "gh",
            "api",
            "/repos/owner/repo/issues/1/comments",
            "--method",
            "POST",
            "--input",
            "-",
        ]

        # Check input data
        assert call_args[1]["input"] == json.dumps({"body": "Test comment"})

        # Verify response structure
        assert result["id"] == 123456789
        assert result["html_url"] == "https://github.com/owner/repo/pull/1#issuecomment-123456789"
        assert result["body"] == "Test comment"
        assert result["created_at"] == "2024-01-01T12:00:00Z"
        assert result["updated_at"] == "2024-01-01T12:00:00Z"
        assert result["user"] == "testuser"
        assert result["node_id"] == "IC_kwDOABCD12345"

    @patch("subprocess.run")
    def test_post_comment_api_failure(self, mock_run):
        """Test comment posting failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr="API Error: Not Found")

        with pytest.raises(GitHubAPIError) as exc_info:
            self.client.post_comment("https://github.com/owner/repo/pull/1", "Test comment")

        assert "Failed to post comment via API" in str(exc_info.value)

    @patch("subprocess.run")
    def test_post_comment_json_parse_error(self, mock_run):
        """Test handling of malformed JSON response."""
        mock_run.return_value = MagicMock(returncode=0, stdout="invalid json")

        with pytest.raises(GitHubAPIError) as exc_info:
            self.client.post_comment("https://github.com/owner/repo/pull/1", "Test comment")

        assert "Failed to parse GitHub API response" in str(exc_info.value)

    @patch("subprocess.run")
    def test_post_comment_timeout(self, mock_run):
        """Test timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("gh", 30)

        with pytest.raises(GitHubAPIError) as exc_info:
            self.client.post_comment("https://github.com/owner/repo/pull/1", "Test comment")

        assert "GitHub API comment posting timed out" in str(exc_info.value)

    @patch("subprocess.run")
    def test_get_comment_success(self, mock_run):
        """Test successful comment retrieval."""
        mock_response = {
            "id": 123456789,
            "html_url": "https://github.com/owner/repo/pull/1#issuecomment-123456789",
            "body": "Retrieved comment",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "user": {"login": "testuser"},
            "node_id": "IC_kwDOABCD12345",
        }

        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(mock_response))

        result = self.client.get_comment("https://github.com/owner/repo/pull/1", 123456789)

        # Verify the API call
        mock_run.assert_called_once_with(
            ["gh", "api", "/repos/owner/repo/issues/comments/123456789"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Verify response
        assert result["id"] == 123456789
        assert result["body"] == "Retrieved comment"

    @patch("subprocess.run")
    def test_get_latest_comments_success(self, mock_run):
        """Test successful latest comments retrieval."""
        mock_response = [
            {
                "id": 123456789,
                "html_url": "https://github.com/owner/repo/pull/1#issuecomment-123456789",
                "body": "Latest comment",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "user": {"login": "testuser"},
                "node_id": "IC_kwDOABCD12345",
            }
        ]

        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(mock_response))

        result = self.client.get_latest_comments("https://github.com/owner/repo/pull/1", 5)

        # Verify the API call
        mock_run.assert_called_once_with(
            [
                "gh",
                "api",
                "/repos/owner/repo/issues/1/comments",
                "--jq",
                "sort_by(.created_at) | reverse | .[:5]",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Verify response
        assert len(result) == 1
        assert result[0]["id"] == 123456789
        assert result[0]["body"] == "Latest comment"

    def test_parse_pr_url_valid(self):
        """Test valid PR URL parsing."""
        url = "https://github.com/owner/repo/pull/123"
        owner, repo, pr_number = self.client.parse_pr_url(url)

        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == "123"

    def test_parse_pr_url_invalid(self):
        """Test invalid PR URL handling."""
        invalid_urls = [
            "",
            "not-a-url",
            "https://example.com/owner/repo/pull/123",
            "https://github.com/owner/repo/issues/123",
            "https://github.com/owner/repo/pull/abc",
        ]

        for url in invalid_urls:
            with pytest.raises(InvalidPRUrlError):
                self.client.parse_pr_url(url)

    def test_response_structure_consistency(self):
        """Test that all comment-related methods return consistent structure."""
        expected_fields = {"id", "html_url", "body", "created_at", "updated_at", "user", "node_id"}

        # Mock response for testing
        mock_response = {
            "id": 123456789,
            "html_url": "https://github.com/owner/repo/pull/1#issuecomment-123456789",
            "body": "Test comment",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "user": {"login": "testuser"},
            "node_id": "IC_kwDOABCD12345",
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(mock_response))

            # Test post_comment response structure
            result = self.client.post_comment(
                "https://github.com/owner/repo/pull/1", "Test comment"
            )

            assert set(result.keys()) == expected_fields

            # Test get_comment response structure
            result = self.client.get_comment("https://github.com/owner/repo/pull/1", 123456789)

            assert set(result.keys()) == expected_fields

    @patch("subprocess.run")
    def test_error_message_quality(self, mock_run):
        """Test that error messages are informative."""
        # Test API error
        mock_run.return_value = MagicMock(
            returncode=1, stderr="HTTP 404: Not Found (https://docs.github.com/rest)"
        )

        with pytest.raises(GitHubAPIError) as exc_info:
            self.client.post_comment("https://github.com/owner/repo/pull/1", "Test comment")

        error_message = str(exc_info.value)
        assert "Failed to post comment via API" in error_message
        assert "HTTP 404: Not Found" in error_message

    def test_backward_compatibility_note(self):
        """Document backward compatibility considerations."""
        # This test serves as documentation for the API changes

        # OLD: post_comment returned True/False
        # NEW: post_comment returns detailed metadata dictionary

        # Code using the old API should be updated to handle the new response:
        # OLD: if client.post_comment(url, comment):
        # NEW: result = client.post_comment(url, comment)
        #      if result and result.get("id"):

        # The new API provides much more information:
        # - comment ID for future reference
        # - direct HTML URL for linking
        # - timestamps for tracking
        # - user information
        # - GraphQL node ID for advanced operations

        assert True  # This test always passes - it's for documentation

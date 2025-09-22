"""Integration tests for GitHub CLI interaction."""

import unittest
import json
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coderabbit_fetcher.github_client import GitHubClient
from coderabbit_fetcher.exceptions import (
    GitHubAuthenticationError,
    InvalidPRUrlError,
    NetworkError,
    RateLimitError
)
from tests.fixtures.github_responses import (
    MOCK_SUCCESS_RESPONSES,
    MOCK_GH_ERROR_RESPONSES,
    get_mock_response,
    MOCK_GH_COMMENTS_RESPONSE,
    MOCK_GH_PR_RESPONSE
)


class TestGitHubIntegration(unittest.TestCase):
    """Test GitHub CLI integration functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = GitHubClient()
        self.sample_pr_url = "https://github.com/owner/repo/pull/123"

    @patch('subprocess.run')
    def test_check_authentication_success(self, mock_run):
        """Test successful authentication check."""
        # Clear cached authentication state
        self.client._authenticated = None
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=MOCK_SUCCESS_RESPONSES["gh_auth_status"]["stdout"],
            stderr=""
        )

        is_authenticated = self.client.check_authentication()

        self.assertTrue(is_authenticated)
        mock_run.assert_called_once()

        # Verify the command was correct
        call_args = mock_run.call_args
        self.assertIn('gh', call_args[0][0])
        self.assertIn('auth', call_args[0][0])
        self.assertIn('status', call_args[0][0])

    @patch('subprocess.run')
    def test_check_authentication_failure(self, mock_run):
        """Test authentication failure."""
        # Clear cached authentication state
        self.client._authenticated = None
        
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr=MOCK_GH_ERROR_RESPONSES["authentication_error"]["stderr"]
        )

        with self.assertRaises(GitHubAuthenticationError) as context:
            self.client.check_authentication()

        self.assertIn("authentication", str(context.exception).lower())

    @patch('subprocess.run')
    def test_fetch_pr_comments_success(self, mock_run):
        """Test successful PR comments fetching."""
        # Mock successful responses for both PR data and comments
        mock_responses = [
            # First call: get PR data
            MagicMock(
                returncode=0,
                stdout=json.dumps(MOCK_GH_PR_RESPONSE),
                stderr=""
            ),
            # Second call: get comments
            MagicMock(
                returncode=0,
                stdout=json.dumps(MOCK_GH_COMMENTS_RESPONSE),
                stderr=""
            )
        ]
        mock_run.side_effect = mock_responses

        result = self.client.fetch_pr_comments(self.sample_pr_url)

        self.assertIsInstance(result, dict)
        self.assertIn("pr_data", result)
        self.assertIn("comments", result)
        self.assertEqual(len(result["comments"]), len(MOCK_GH_COMMENTS_RESPONSE))

        # Verify both commands were called
        self.assertEqual(mock_run.call_count, 2)

    @patch('subprocess.run')
    def test_fetch_pr_comments_invalid_url(self, mock_run):
        """Test PR comments fetching with invalid URL."""
        invalid_url = "not-a-valid-url"

        with self.assertRaises(InvalidPRUrlError):
            self.client.fetch_pr_comments(invalid_url)

        # Should not make any subprocess calls for invalid URL
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_fetch_pr_comments_not_found(self, mock_run):
        """Test PR comments fetching with non-existent PR."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr=MOCK_GH_ERROR_RESPONSES["not_found_error"]["stderr"]
        )

        with self.assertRaises(InvalidPRUrlError) as context:
            self.client.fetch_pr_comments(self.sample_pr_url)

        self.assertIn("404", str(context.exception))

    @patch('subprocess.run')
    def test_fetch_pr_comments_rate_limit(self, mock_run):
        """Test PR comments fetching with rate limit."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr=MOCK_GH_ERROR_RESPONSES["rate_limit_error"]["stderr"]
        )

        with self.assertRaises(RateLimitError) as context:
            self.client.fetch_pr_comments(self.sample_pr_url)

        self.assertIn("rate limit", str(context.exception).lower())

    @patch('subprocess.run')
    def test_fetch_pr_comments_network_error(self, mock_run):
        """Test PR comments fetching with network error."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr=MOCK_GH_ERROR_RESPONSES["network_error"]["stderr"]
        )

        with self.assertRaises(NetworkError):
            self.client.fetch_pr_comments(self.sample_pr_url)

    @patch('subprocess.run')
    def test_parse_pr_url_valid(self, mock_run):
        """Test URL parsing with valid GitHub PR URLs."""
        valid_urls = [
            "https://github.com/owner/repo/pull/123",
            "https://github.com/test-user/test-repo/pull/1",
            "https://github.com/org_name/repo.name/pull/999999"
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                owner, repo, pr_number = self.client._parse_pr_url(url)
                self.assertIsInstance(owner, str)
                self.assertIsInstance(repo, str)
                self.assertIsInstance(pr_number, int)
                self.assertGreater(pr_number, 0)

    def test_parse_pr_url_invalid(self):
        """Test URL parsing with invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "https://gitlab.com/owner/repo/pull/123",
            "https://github.com/owner",
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/issues/123",
            "https://github.com/owner/repo/pull/abc"
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(InvalidPRUrlError):
                    self.client._parse_pr_url(url)

    @patch('subprocess.run')
    def test_check_rate_limits(self, mock_run):
        """Test rate limit checking."""
        from tests.fixtures.github_responses import MOCK_RATE_LIMIT_RESPONSE

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(MOCK_RATE_LIMIT_RESPONSE),
            stderr=""
        )

        rate_limits = self.client.check_rate_limits()

        self.assertIsInstance(rate_limits, dict)
        self.assertIn("core", rate_limits["resources"])
        self.assertIn("remaining", rate_limits["resources"]["core"])

        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_post_comment_success(self, mock_run):
        """Test successful comment posting."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"id": 12345, "body": "Test comment"}',
            stderr=""
        )

        result = self.client.post_comment(
            pr_url=self.sample_pr_url,
            comment="Test comment"
        )

        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertEqual(result["body"], "Test comment")

        mock_run.assert_called_once()

        # Verify command structure
        call_args = mock_run.call_args[0][0]
        self.assertIn('gh', call_args)
        self.assertIn('api', call_args)

    @patch('subprocess.run')
    def test_post_comment_failure(self, mock_run):
        """Test comment posting failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="gh: HTTP 403: You do not have permission"
        )

        with self.assertRaises(Exception):  # Should raise some form of error
            self.client.post_comment(
                pr_url=self.sample_pr_url,
                comment="Test comment"
            )

    @patch('subprocess.run')
    def test_github_cli_timeout(self, mock_run):
        """Test GitHub CLI timeout handling."""
        # Clear cached authentication state
        self.client._authenticated = None
        
        # Simulate a timeout
        mock_run.side_effect = subprocess.TimeoutExpired('gh', 30)

        with self.assertRaises(GitHubAuthenticationError):  # Should raise timeout-related error
            self.client.check_authentication()

    @patch('subprocess.run')
    def test_validate_github_cli_available(self, mock_run):
        """Test GitHub CLI availability validation."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=MOCK_SUCCESS_RESPONSES["gh_version"]["stdout"],
            stderr=""
        )

        result = self.client.validate()

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["issues"]), 0)

        mock_run.assert_called()

    @patch('subprocess.run')
    def test_validate_github_cli_not_available(self, mock_run):
        """Test validation when GitHub CLI is not available."""
        mock_run.side_effect = FileNotFoundError("gh command not found")

        result = self.client.validate()

        self.assertFalse(result["valid"])
        self.assertGreater(len(result["issues"]), 0)
        self.assertIn("GitHub CLI", result["issues"][0])

    @patch('subprocess.run')
    def test_retry_logic_on_transient_failure(self, mock_run):
        """Test retry logic on transient failures."""
        # First call fails, second succeeds
        mock_responses = [
            MagicMock(
                returncode=1,
                stdout="",
                stderr="network error"
            ),
            MagicMock(
                returncode=0,
                stdout=MOCK_SUCCESS_RESPONSES["gh_auth_status"]["stdout"],
                stderr=""
            )
        ]
        mock_run.side_effect = mock_responses

        # This should succeed after retry
        result = self.client._execute_gh_command(['gh', 'auth', 'status'])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(mock_run.call_count, 2)

    @patch('subprocess.run')
    def test_json_parsing_error_handling(self, mock_run):
        """Test handling of malformed JSON responses."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"malformed": json',  # Invalid JSON
            stderr=""
        )

        with self.assertRaises(Exception):  # Should handle JSON parsing errors
            self.client.fetch_pr_comments(self.sample_pr_url)


class TestGitHubIntegrationEdgeCases(unittest.TestCase):
    """Test edge cases in GitHub integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = GitHubClient()

    @patch('subprocess.run')
    def test_empty_comments_response(self, mock_run):
        """Test handling of empty comments response."""
        mock_responses = [
            # PR data
            MagicMock(
                returncode=0,
                stdout=json.dumps(MOCK_GH_PR_RESPONSE),
                stderr=""
            ),
            # Empty comments
            MagicMock(
                returncode=0,
                stdout="[]",
                stderr=""
            )
        ]
        mock_run.side_effect = mock_responses

        result = self.client.fetch_pr_comments("https://github.com/owner/repo/pull/123")

        self.assertIn("comments", result)
        self.assertEqual(len(result["comments"]), 0)

    @patch('subprocess.run')
    def test_large_comments_response(self, mock_run):
        """Test handling of large comments response."""
        from tests.fixtures.github_responses import MOCK_LARGE_COMMENTS_RESPONSE

        mock_responses = [
            # PR data
            MagicMock(
                returncode=0,
                stdout=json.dumps(MOCK_GH_PR_RESPONSE),
                stderr=""
            ),
            # Large comments response
            MagicMock(
                returncode=0,
                stdout=json.dumps(MOCK_LARGE_COMMENTS_RESPONSE),
                stderr=""
            )
        ]
        mock_run.side_effect = mock_responses

        result = self.client.fetch_pr_comments("https://github.com/owner/repo/pull/123")

        self.assertIn("comments", result)
        self.assertEqual(len(result["comments"]), len(MOCK_LARGE_COMMENTS_RESPONSE))

    @patch('subprocess.run')
    def test_unicode_content_handling(self, mock_run):
        """Test handling of Unicode content in comments."""
        unicode_comment = {
            "id": 123,
            "author": {"login": "coderabbitai[bot]"},
            "body": "コメント with émojis 🚀🔥💻 and special chars: <>&\"'",
            "createdAt": "2025-08-27T17:00:00Z"
        }

        mock_responses = [
            # PR data
            MagicMock(
                returncode=0,
                stdout=json.dumps(MOCK_GH_PR_RESPONSE),
                stderr=""
            ),
            # Unicode comments
            MagicMock(
                returncode=0,
                stdout=json.dumps([unicode_comment]),
                stderr=""
            )
        ]
        mock_run.side_effect = mock_responses

        result = self.client.fetch_pr_comments("https://github.com/owner/repo/pull/123")

        self.assertIn("comments", result)
        self.assertEqual(len(result["comments"]), 1)
        self.assertIn("🚀", result["comments"][0]["body"])

    @patch('subprocess.run')
    def test_command_injection_prevention(self, mock_run):
        """Test prevention of command injection in PR URLs."""
        malicious_urls = [
            "https://github.com/owner/repo/pull/123; rm -rf /",
            "https://github.com/owner/repo/pull/123 && cat /etc/passwd",
            "https://github.com/owner/repo/pull/123`whoami`"
        ]

        for url in malicious_urls:
            with self.subTest(url=url):
                with self.assertRaises(InvalidPRUrlError):
                    self.client.fetch_pr_comments(url)

                # Ensure no subprocess calls were made
                mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_concurrent_requests_handling(self, mock_run):
        """Test handling of concurrent requests (simplified simulation)."""
        import threading
        import time

        # Mock response that takes some time
        def slow_response(*args, **kwargs):
            time.sleep(0.1)  # Simulate network delay
            return MagicMock(
                returncode=0,
                stdout=json.dumps(MOCK_GH_PR_RESPONSE),
                stderr=""
            )

        mock_run.side_effect = slow_response

        results = []
        errors = []

        def fetch_comments():
            try:
                result = self.client.fetch_pr_comments("https://github.com/owner/repo/pull/123")
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=fetch_comments)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
        self.assertGreater(len(results), 0)


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""
Safe test suite for GitHubClient that works in CI environments.

This test suite uses comprehensive mocking to avoid dependencies on:
- GitHub CLI (gh) installation
- GitHub authentication
- Network connectivity
- External services

Designed for reliable CI/CD pipeline execution.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock

from coderabbit_fetcher.github_client import GitHubClient, GitHubAPIError
from coderabbit_fetcher.exceptions import GitHubAuthenticationError, InvalidPRUrlError


class TestGitHubClientSafeInitialization:
    """Test GitHubClient initialization with mocked dependencies."""

    def test_successful_initialization(self):
        """Test successful GitHubClient initialization with mocked authentication."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            client = GitHubClient()
            assert client is not None
            assert hasattr(client, '_authenticated')

    def test_missing_gh_command(self):
        """Test handling of missing gh command."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("gh command not found")

            with pytest.raises(GitHubAuthenticationError) as exc_info:
                GitHubClient()

            assert "not installed or not in PATH" in str(exc_info.value)

    def test_authentication_failure(self):
        """Test handling of authentication failure."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Not authenticated", stdout="")

            with pytest.raises(GitHubAuthenticationError) as exc_info:
                GitHubClient()

            assert "not authenticated" in str(exc_info.value)

    def test_command_timeout(self):
        """Test handling of command timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("gh", 10)

            with pytest.raises(GitHubAuthenticationError) as exc_info:
                GitHubClient()

            assert "timed out" in str(exc_info.value)

    def test_unexpected_error(self):
        """Test handling of unexpected errors during initialization."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(GitHubAuthenticationError) as exc_info:
                GitHubClient()

            assert "Failed to check GitHub CLI authentication" in str(exc_info.value)


class TestGitHubClientURLParsing:
    """Test URL parsing functionality (no external dependencies)."""

    @pytest.fixture
    def client(self):
        """Create a GitHubClient with mocked authentication."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            return GitHubClient()

    def test_valid_pr_url(self, client):
        """Test parsing of valid PR URLs."""
        test_cases = [
            ("https://github.com/owner/repo/pull/123", ("owner", "repo", "123")),
            ("http://github.com/test/project/pull/456", ("test", "project", "456")),
            ("https://github.com/org-name/repo-name/pull/789", ("org-name", "repo-name", "789")),
        ]

        for url, expected in test_cases:
            result = client.parse_pr_url(url)
            assert result == expected

    def test_invalid_pr_urls(self, client):
        """Test handling of invalid PR URLs."""
        invalid_urls = [
            "",  # Empty URL
            "invalid-url",  # Not a URL
            "https://example.com/owner/repo/pull/123",  # Not GitHub
            "https://github.com/owner/repo/issues/123",  # Issues, not PR
            "https://github.com/owner/repo/pull/abc",  # Non-numeric PR number
            "https://github.com/owner/repo/pull/",  # Missing PR number
            "ftp://github.com/owner/repo/pull/123",  # Wrong protocol
        ]

        for url in invalid_urls:
            with pytest.raises(InvalidPRUrlError):
                client.parse_pr_url(url)


class TestGitHubClientAuthenticationMethods:
    """Test authentication-related methods with mocking."""

    def test_is_authenticated_cached_result(self):
        """Test that is_authenticated returns cached result."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            client = GitHubClient()

            # First call should use cached result
            assert client.is_authenticated() is True

            # Subsequent calls should not trigger subprocess
            mock_run.reset_mock()
            assert client.is_authenticated() is True
            mock_run.assert_not_called()

    def test_check_authentication_success(self):
        """Test successful authentication check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            client = GitHubClient()
            result = client.check_authentication()

            assert result is True
            assert client._authenticated is True

    def test_check_authentication_failure(self):
        """Test failed authentication check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Not logged in", stdout="")

            with pytest.raises(GitHubAuthenticationError):
                GitHubClient()


class TestCIEnvironmentCompatibility:
    """Test compatibility with various CI environments."""

    def test_github_actions_environment(self):
        """Test behavior in GitHub Actions environment."""
        # Simulate GitHub Actions where gh might not be configured
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("gh: command not found")

            with pytest.raises(GitHubAuthenticationError) as exc_info:
                GitHubClient()

            error_msg = str(exc_info.value)
            assert "not installed" in error_msg or "not in PATH" in error_msg

    def test_docker_environment(self):
        """Test behavior in Docker container environment."""
        # Simulate Docker environment with limited tools
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = OSError("Operation not permitted")

            with pytest.raises(GitHubAuthenticationError):
                GitHubClient()

    def test_restricted_environment(self):
        """Test behavior in restricted environments."""
        # Simulate environment where subprocess is restricted
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = PermissionError("Permission denied")

            with pytest.raises(GitHubAuthenticationError):
                GitHubClient()

    @pytest.mark.parametrize("error_type,error_message", [
        (FileNotFoundError, "gh: command not found"),
        (PermissionError, "Permission denied"),
        (OSError, "Operation not permitted"),
        (subprocess.TimeoutExpired, None),  # Special case for timeout
    ])
    def test_various_system_errors(self, error_type, error_message):
        """Test handling of various system-level errors."""
        with patch('subprocess.run') as mock_run:
            if error_type == subprocess.TimeoutExpired:
                mock_run.side_effect = subprocess.TimeoutExpired("gh", 10)
            else:
                mock_run.side_effect = error_type(error_message)

            with pytest.raises(GitHubAuthenticationError):
                GitHubClient()


class TestGitHubClientValidation:
    """Test the validation methods."""

    def test_validate_github_cli_not_installed(self):
        """Test validation when gh is not installed."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")

            # Create client with mocked successful auth for this test
            with patch.object(GitHubClient, 'check_authentication'):
                client = GitHubClient()
                result = client.validate_github_cli()

            assert result["gh_installed"] is False
            assert "not installed" in " ".join(result["issues"])

    def test_validate_github_cli_installed_not_authenticated(self):
        """Test validation when gh is installed but not authenticated."""
        with patch('subprocess.run') as mock_run:
            def side_effect(cmd, **kwargs):
                if cmd[1] == "--version":
                    return MagicMock(returncode=0, stdout="gh version 2.0.0")
                elif cmd[1] == "auth":
                    return MagicMock(returncode=1, stderr="Not authenticated")
                return MagicMock(returncode=1)

            mock_run.side_effect = side_effect

            # Create client with mocked successful auth for this test
            with patch.object(GitHubClient, 'check_authentication'):
                client = GitHubClient()
                result = client.validate_github_cli()

            assert result["gh_installed"] is True
            assert result["authenticated"] is False
            assert "not authenticated" in " ".join(result["issues"])


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

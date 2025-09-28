"""Unit tests for comment posting functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from coderabbit_fetcher.comment_poster import (
    CommentPoster,
    ResolutionRequestConfig,
    ResolutionRequestManager,
    CommentPostingError,
    InvalidCommentError,
    PRUrlValidationError
)
# GitHubClient will be implemented in Task 12 - using Mock for testing


class TestResolutionRequestConfig:
    """Test cases for ResolutionRequestConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ResolutionRequestConfig()

        assert config.resolved_marker == "🔒 CODERABBIT_RESOLVED 🔒"
        assert "@coderabbitai" in config.request_template
        assert config.include_context is True
        assert config.max_comment_length == 65536

    def test_custom_config(self):
        """Test custom configuration."""
        config = ResolutionRequestConfig(
            resolved_marker="✅ CUSTOM ✅",
            request_template="Custom template {marker}",
            include_context=False,
            custom_prefix="PREFIX:",
            custom_suffix="SUFFIX"
        )

        assert config.resolved_marker == "✅ CUSTOM ✅"
        assert config.request_template == "Custom template {marker}"
        assert config.include_context is False
        assert config.custom_prefix == "PREFIX:"
        assert config.custom_suffix == "SUFFIX"

    def test_generate_message_basic(self):
        """Test basic message generation."""
        config = ResolutionRequestConfig(
            resolved_marker="🔒 TEST 🔒",
            request_template="@coderabbitai Test {marker}"
        )

        message = config.generate_message()

        assert "@coderabbitai Test 🔒 TEST 🔒" == message

    def test_generate_message_with_context(self):
        """Test message generation with context."""
        config = ResolutionRequestConfig(
            resolved_marker="🔒 TEST 🔒",
            request_template="@coderabbitai Test {marker}",
            include_context=True
        )

        message = config.generate_message("Additional context here")

        assert "@coderabbitai Test 🔒 TEST 🔒" in message
        assert "Context: Additional context here" in message

    def test_generate_message_with_prefix_suffix(self):
        """Test message generation with prefix and suffix."""
        config = ResolutionRequestConfig(
            resolved_marker="🔒 TEST 🔒",
            request_template="@coderabbitai Test {marker}",
            custom_prefix="PREFIX",
            custom_suffix="SUFFIX"
        )

        message = config.generate_message()

        assert message.startswith("PREFIX")
        assert message.endswith("SUFFIX")
        assert "@coderabbitai Test 🔒 TEST 🔒" in message

    def test_generate_message_without_context(self):
        """Test message generation with context disabled."""
        config = ResolutionRequestConfig(
            resolved_marker="🔒 TEST 🔒",
            request_template="@coderabbitai Test {marker}",
            include_context=False
        )

        message = config.generate_message("This context should be ignored")

        assert "Context:" not in message
        assert "This context should be ignored" not in message

    def test_generate_message_length_truncation(self):
        """Test message truncation when too long."""
        config = ResolutionRequestConfig(
            resolved_marker="🔒 TEST 🔒",
            request_template="@coderabbitai Test {marker}",
            max_comment_length=100,
            include_context=True
        )

        long_context = "x" * 200
        message = config.generate_message(long_context)

        assert len(message) <= 100
        assert "@coderabbitai Test 🔒 TEST 🔒" in message

    def test_generate_message_too_long_error(self):
        """Test error when message is too long even without context."""
        config = ResolutionRequestConfig(
            resolved_marker="🔒 TEST 🔒",
            request_template="x" * 100,  # Very long template
            max_comment_length=50,
            include_context=False
        )

        with pytest.raises(InvalidCommentError):
            config.generate_message()

    def test_validate_marker_valid(self):
        """Test marker validation with valid marker."""
        config = ResolutionRequestConfig(resolved_marker="🔒 VALID_MARKER 🔒")

        result = config.validate_marker()

        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_validate_marker_empty(self):
        """Test marker validation with empty marker."""
        config = ResolutionRequestConfig(resolved_marker="")

        result = config.validate_marker()

        assert result["valid"] is False
        assert "cannot be empty" in result["issues"][0]

    def test_validate_marker_too_short(self):
        """Test marker validation with too short marker."""
        config = ResolutionRequestConfig(resolved_marker="OK")

        result = config.validate_marker()

        assert result["valid"] is False
        assert "at least 3 characters" in result["issues"][0]

    def test_validate_marker_too_long(self):
        """Test marker validation with too long marker."""
        config = ResolutionRequestConfig(resolved_marker="x" * 101)

        result = config.validate_marker()

        assert result["valid"] is False
        assert "should not exceed 100 characters" in result["issues"][0]

    def test_validate_marker_github_mention(self):
        """Test marker validation with GitHub mentions."""
        config = ResolutionRequestConfig(resolved_marker="@github-user RESOLVED")

        result = config.validate_marker()

        assert result["valid"] is False
        assert "GitHub mentions" in result["issues"][0]


class TestCommentPoster:
    """Test cases for CommentPoster."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_github_client = Mock()  # Mock GitHub client
        self.mock_github_client.is_authenticated.return_value = True

        self.config = ResolutionRequestConfig(
            resolved_marker="🔒 TEST 🔒",
            request_template="@coderabbitai Test {marker}"
        )

        self.poster = CommentPoster(self.mock_github_client, self.config)

    def test_initialization_default_config(self):
        """Test initialization with default configuration."""
        poster = CommentPoster(self.mock_github_client)

        assert poster.github_client == self.mock_github_client
        assert poster.config.resolved_marker == "🔒 CODERABBIT_RESOLVED 🔒"

    def test_initialization_custom_config(self):
        """Test initialization with custom configuration."""
        assert self.poster.config.resolved_marker == "🔒 TEST 🔒"

    def test_initialization_invalid_config(self):
        """Test initialization with invalid configuration."""
        invalid_config = ResolutionRequestConfig(resolved_marker="")

        with pytest.raises(InvalidCommentError):
            CommentPoster(self.mock_github_client, invalid_config)

    def test_post_resolution_request_success(self):
        """Test successful resolution request posting."""
        pr_url = "https://github.com/owner/repo/pull/123"
        mock_response = {
            "id": 12345,
            "html_url": "https://github.com/owner/repo/pull/123#issuecomment-12345",
            "created_at": "2023-01-01T00:00:00Z"
        }
        self.mock_github_client.post_comment.return_value = mock_response

        result = self.poster.post_resolution_request(pr_url, "Test context")

        assert result["success"] is True
        assert result["comment_id"] == 12345
        assert result["pr_url"] == pr_url
        assert result["context_included"] is True
        assert "Test context" in result["message"]

        # Verify GitHub client was called
        self.mock_github_client.post_comment.assert_called_once()
        call_args = self.mock_github_client.post_comment.call_args
        assert call_args[0][0] == pr_url
        assert "@coderabbitai Test 🔒 TEST 🔒" in call_args[0][1]

    def test_post_resolution_request_invalid_url(self):
        """Test posting with invalid PR URL."""
        invalid_url = "https://not-github.com/owner/repo/pull/123"

        with pytest.raises(PRUrlValidationError):
            self.poster.post_resolution_request(invalid_url)

    def test_post_resolution_request_github_client_failure(self):
        """Test posting failure due to GitHub client error."""
        pr_url = "https://github.com/owner/repo/pull/123"
        self.mock_github_client.post_comment.side_effect = Exception("API Error")

        with pytest.raises(CommentPostingError) as exc_info:
            self.poster.post_resolution_request(pr_url)

        assert "Failed to post comment" in str(exc_info.value)
        assert "API Error" in str(exc_info.value)

    def test_generate_resolution_request(self):
        """Test resolution request generation."""
        result = self.poster.generate_resolution_request("Test context")

        assert "@coderabbitai Test 🔒 TEST 🔒" in result
        assert "Context: Test context" in result

    def test_batch_post_resolution_requests(self):
        """Test batch posting to multiple PRs."""
        pr_urls = [
            "https://github.com/owner/repo/pull/123",
            "https://github.com/owner/repo/pull/124",
            "https://github.com/owner/repo/pull/125"
        ]

        context_per_url = {
            pr_urls[0]: "Context for PR 123",
            pr_urls[1]: "Context for PR 124"
        }

        # Mock successful responses
        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.poster.batch_post_resolution_requests(pr_urls, context_per_url)

        assert result["total_urls"] == 3
        assert result["success_count"] == 3
        assert result["failure_count"] == 0
        assert result["success_rate"] == 1.0
        assert len(result["successful_posts"]) == 3
        assert len(result["failed_posts"]) == 0

    def test_batch_post_with_failures(self):
        """Test batch posting with some failures."""
        pr_urls = [
            "https://github.com/owner/repo/pull/123",
            "invalid-url",
            "https://github.com/owner/repo/pull/125"
        ]

        # Mock successful response for valid URLs
        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.poster.batch_post_resolution_requests(pr_urls)

        assert result["total_urls"] == 3
        assert result["success_count"] == 2
        assert result["failure_count"] == 1
        assert result["success_rate"] == 2/3
        assert len(result["successful_posts"]) == 2
        assert len(result["failed_posts"]) == 1
        assert "invalid-url" in result["failed_posts"][0]["pr_url"]

    def test_validate_resolution_request_valid(self):
        """Test validation of valid resolution request."""
        result = self.poster.validate_resolution_request("Test context")

        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["message_length"] > 0
        assert len(result["message_preview"]) > 0

    def test_validate_resolution_request_invalid_config(self):
        """Test validation with invalid configuration."""
        # Create poster with invalid config
        invalid_config = ResolutionRequestConfig(resolved_marker="")

        # Override the validation that happens in __init__
        poster = CommentPoster.__new__(CommentPoster)
        poster.github_client = self.mock_github_client
        poster.config = invalid_config

        result = poster.validate_resolution_request()

        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_validate_resolution_request_with_warnings(self):
        """Test validation that generates warnings."""
        long_context = "x" * 1500  # Long context

        result = self.poster.validate_resolution_request(long_context)

        assert len(result["warnings"]) > 0
        assert "context is quite long" in result["warnings"][0]

    def test_update_config(self):
        """Test configuration update."""
        self.poster.update_config(
            resolved_marker="🔒 UPDATED 🔒",
            include_context=False
        )

        assert self.poster.config.resolved_marker == "🔒 UPDATED 🔒"
        assert self.poster.config.include_context is False

    def test_update_config_invalid_parameter(self):
        """Test configuration update with invalid parameter."""
        with pytest.raises(ValueError):
            self.poster.update_config(invalid_param="value")

    def test_get_posting_statistics(self):
        """Test posting statistics retrieval."""
        stats = self.poster.get_posting_statistics()

        assert "max_comment_length" in stats
        assert "resolved_marker" in stats
        assert "github_client_authenticated" in stats
        assert stats["github_client_authenticated"] is True
        assert "config_valid" in stats

    def test_validate_pr_url_valid(self):
        """Test valid PR URL validation."""
        valid_urls = [
            "https://github.com/owner/repo/pull/123",
            "http://github.com/owner/repo/pull/456",
            "https://www.github.com/owner/repo/pull/789"
        ]

        for url in valid_urls:
            # Should not raise an exception
            self.poster._validate_pr_url(url)

    def test_validate_pr_url_invalid(self):
        """Test invalid PR URL validation."""
        invalid_urls = [
            "",  # Empty
            "not-a-url",  # Not a URL
            "ftp://github.com/owner/repo/pull/123",  # Wrong scheme
            "https://gitlab.com/owner/repo/pull/123",  # Wrong domain
            "https://github.com/owner/repo/issues/123",  # Issues, not pull
            "https://github.com/owner/repo/pull/abc",  # Invalid PR number
            "https://github.com/owner/repo/pull/-123",  # Negative PR number
        ]

        for url in invalid_urls:
            with pytest.raises(PRUrlValidationError):
                self.poster._validate_pr_url(url)

    def test_validate_comment_content_valid(self):
        """Test valid comment content validation."""
        valid_content = "This is a valid comment with @coderabbitai mention"

        issues = self.poster._validate_comment_content(valid_content, raise_on_error=False)

        assert len(issues) == 0

    def test_validate_comment_content_invalid(self):
        """Test invalid comment content validation."""
        invalid_contents = [
            "",  # Empty
            "   ",  # Whitespace only
            "x" * 70000,  # Too long
            "Comment with @everyone mention",  # Problematic mention
            "Code ```block``` with ```unmatched marker",  # Unbalanced markdown
            "Comment\n\n\n\nwith excessive newlines"  # Excessive blank lines
        ]

        for content in invalid_contents:
            issues = self.poster._validate_comment_content(content, raise_on_error=False)
            assert len(issues) > 0

    def test_validate_comment_content_raise_on_error(self):
        """Test comment validation with raise_on_error=True."""
        invalid_content = ""

        with pytest.raises(InvalidCommentError):
            self.poster._validate_comment_content(invalid_content, raise_on_error=True)

    def test_extract_pr_info(self):
        """Test PR info extraction from URL."""
        pr_url = "https://github.com/owner/repo/pull/123"

        info = self.poster.extract_pr_info(pr_url)

        assert info["owner"] == "owner"
        assert info["repo"] == "repo"
        assert info["pr_number"] == "123"

    def test_extract_pr_info_invalid_url(self):
        """Test PR info extraction from invalid URL."""
        invalid_url = "https://github.com/owner/repo/issues/123"

        with pytest.raises(PRUrlValidationError):
            self.poster.extract_pr_info(invalid_url)


class TestResolutionRequestManager:
    """Test cases for ResolutionRequestManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_github_client = Mock()  # Mock GitHub client
        self.mock_github_client.is_authenticated.return_value = True

        self.config = ResolutionRequestConfig(
            resolved_marker="🔒 TEST 🔒",
            request_template="@coderabbitai Test {marker}"
        )

        self.manager = ResolutionRequestManager(self.mock_github_client, self.config)

    def test_initialization(self):
        """Test manager initialization."""
        assert self.manager.github_client == self.mock_github_client
        assert isinstance(self.manager.poster, CommentPoster)

    def test_request_resolution_for_comments(self):
        """Test requesting resolution for specific comments."""
        pr_url = "https://github.com/owner/repo/pull/123"
        comment_ids = ["comment1", "comment2", "comment3"]

        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.manager.request_resolution_for_comments(pr_url, comment_ids)

        assert result["success"] is True
        assert "comment1, comment2, comment3" in result["message"]

    def test_request_resolution_for_many_comments(self):
        """Test requesting resolution for many comments (truncation)."""
        pr_url = "https://github.com/owner/repo/pull/123"
        comment_ids = [f"comment{i}" for i in range(15)]  # More than 10

        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.manager.request_resolution_for_comments(pr_url, comment_ids)

        assert result["success"] is True
        assert "5 more comments" in result["message"]

    def test_request_resolution_for_numeric_comment_ids(self):
        """Test requesting resolution with numeric comment IDs."""
        pr_url = "https://github.com/owner/repo/pull/123"
        comment_ids = [123456, 789012, 345678]  # Numeric IDs

        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.manager.request_resolution_for_comments(pr_url, comment_ids)

        assert result["success"] is True
        assert "123456, 789012, 345678" in result["message"]

    def test_request_resolution_for_mixed_comment_ids(self):
        """Test requesting resolution with mixed string and numeric comment IDs."""
        pr_url = "https://github.com/owner/repo/pull/123"
        comment_ids = ["comment1", 123456, "comment3", 789012]  # Mixed types

        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.manager.request_resolution_for_comments(pr_url, comment_ids)

        assert result["success"] is True
        assert "comment1, 123456, comment3, 789012" in result["message"]

    def test_request_resolution_for_comments_no_summary(self):
        """Test requesting resolution without summary."""
        pr_url = "https://github.com/owner/repo/pull/123"
        comment_ids = ["comment1", "comment2"]

        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.manager.request_resolution_for_comments(pr_url, comment_ids, include_summary=False)

        assert result["success"] is True
        # Should not contain specific comment IDs when summary is disabled
        assert "comment1" not in result["message"]

    def test_request_resolution_with_summary(self):
        """Test requesting resolution with custom summary."""
        pr_url = "https://github.com/owner/repo/pull/123"
        summary = "Fixed authentication bug and updated tests"

        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.manager.request_resolution_with_summary(pr_url, summary)

        assert result["success"] is True
        assert "Summary of changes: Fixed authentication bug" in result["message"]

    def test_validate_and_post_success(self):
        """Test successful validation and posting."""
        pr_url = "https://github.com/owner/repo/pull/123"

        self.mock_github_client.post_comment.return_value = {"id": 12345}

        result = self.manager.validate_and_post(pr_url, "Test context")

        assert result["success"] is True
        assert "validation" in result
        assert "posting" in result
        assert result["validation"]["valid"] is True
        assert result["posting"]["success"] is True

    def test_validate_and_post_validation_failure(self):
        """Test validation failure preventing posting."""
        # Create manager with invalid config
        invalid_config = ResolutionRequestConfig(resolved_marker="")
        manager = ResolutionRequestManager.__new__(ResolutionRequestManager)
        manager.github_client = self.mock_github_client

        # Create poster with invalid config manually
        poster = CommentPoster.__new__(CommentPoster)
        poster.github_client = self.mock_github_client
        poster.config = invalid_config
        manager.poster = poster

        pr_url = "https://github.com/owner/repo/pull/123"

        result = manager.validate_and_post(pr_url)

        assert result["success"] is False
        assert "validation" in result
        assert result["validation"]["valid"] is False
        assert "Validation failed" in result["error"]

    def test_validate_and_post_posting_failure(self):
        """Test posting failure after successful validation."""
        pr_url = "https://github.com/owner/repo/pull/123"

        # Mock posting failure
        self.mock_github_client.post_comment.side_effect = Exception("Posting failed")

        result = self.manager.validate_and_post(pr_url)

        assert result["success"] is False
        assert "validation" in result
        assert result["validation"]["valid"] is True  # Validation should pass
        assert "Posting failed" in result["error"]

    def test_get_config_template(self):
        """Test configuration template retrieval."""
        template = self.manager.get_config_template()

        assert "resolved_marker" in template
        assert "request_template" in template
        assert "custom_options" in template
        assert "default" in template["resolved_marker"]
        assert "examples" in template["resolved_marker"]
        assert "recommendations" in template["resolved_marker"]

    def test_update_poster_config(self):
        """Test updating poster configuration through manager."""
        self.manager.update_poster_config(
            resolved_marker="🔒 UPDATED 🔒",
            include_context=False
        )

        assert self.manager.poster.config.resolved_marker == "🔒 UPDATED 🔒"
        assert self.manager.poster.config.include_context is False


class TestCommentPostingIntegration:
    """Integration tests for comment posting functionality."""

    def test_end_to_end_posting_workflow(self):
        """Test complete posting workflow."""
        # Setup
        mock_github_client = Mock()  # Mock GitHub client
        mock_github_client.is_authenticated.return_value = True
        mock_github_client.post_comment.return_value = {
            "id": 98765,
            "html_url": "https://github.com/test/repo/pull/1#issuecomment-98765",
            "created_at": "2023-12-01T10:00:00Z"
        }

        config = ResolutionRequestConfig(
            resolved_marker="🔒 INTEGRATION_TEST 🔒",
            custom_prefix="🤖 Automated Request:",
            custom_suffix="Thank you for your attention!"
        )

        poster = CommentPoster(mock_github_client, config)

        # Test workflow
        pr_url = "https://github.com/test/repo/pull/1"
        context = "Please verify the authentication fix"

        # 1. Validate request
        validation = poster.validate_resolution_request(context)
        assert validation["valid"] is True

        # 2. Post request
        result = poster.post_resolution_request(pr_url, context)

        # 3. Verify results
        assert result["success"] is True
        assert result["comment_id"] == 98765
        assert result["context_included"] is True
        assert "🤖 Automated Request:" in result["message"]
        assert "🔒 INTEGRATION_TEST 🔒" in result["message"]
        assert "Context: Please verify the authentication fix" in result["message"]
        assert "Thank you for your attention!" in result["message"]

        # 4. Verify GitHub client was called correctly
        mock_github_client.post_comment.assert_called_once()
        call_args = mock_github_client.post_comment.call_args
        assert call_args[0][0] == pr_url
        assert "🔒 INTEGRATION_TEST 🔒" in call_args[0][1]

    def test_error_handling_workflow(self):
        """Test error handling throughout the workflow."""
        # Setup with failing GitHub client
        mock_github_client = Mock()  # Mock GitHub client
        mock_github_client.is_authenticated.return_value = True
        mock_github_client.post_comment.side_effect = Exception("Network error")

        poster = CommentPoster(mock_github_client)

        # Test various error conditions

        # 1. Invalid URL
        with pytest.raises(PRUrlValidationError):
            poster.post_resolution_request("invalid-url")

        # 2. GitHub API failure
        valid_url = "https://github.com/test/repo/pull/1"
        with pytest.raises(CommentPostingError) as exc_info:
            poster.post_resolution_request(valid_url)

        assert "Network error" in str(exc_info.value)

        # 3. Configuration validation
        invalid_config = ResolutionRequestConfig(resolved_marker="")
        with pytest.raises(InvalidCommentError):
            CommentPoster(mock_github_client, invalid_config)

    def test_manager_integration_workflow(self):
        """Test manager integration workflow."""
        # Setup
        mock_github_client = Mock()  # Mock GitHub client
        mock_github_client.is_authenticated.return_value = True
        mock_github_client.post_comment.return_value = {"id": 54321}

        manager = ResolutionRequestManager(mock_github_client)

        # Test different manager methods
        pr_url = "https://github.com/integration/test/pull/42"

        # 1. Request resolution for specific comments
        comment_ids = ["123", "456", "789"]
        result1 = manager.request_resolution_for_comments(pr_url, comment_ids)
        assert result1["success"] is True
        assert "123, 456, 789" in result1["message"]

        # 2. Request resolution with summary
        summary = "Fixed critical security vulnerability"
        result2 = manager.request_resolution_with_summary(pr_url, summary)
        assert result2["success"] is True
        assert summary in result2["message"]

        # 3. Validate and post
        result3 = manager.validate_and_post(pr_url, "Final verification needed")
        assert result3["success"] is True
        assert result3["validation"]["valid"] is True

        # Verify all calls were made
        assert mock_github_client.post_comment.call_count == 3

    def test_configuration_customization_workflow(self):
        """Test configuration customization workflow."""
        mock_github_client = Mock()  # Mock GitHub client
        mock_github_client.is_authenticated.return_value = True
        mock_github_client.post_comment.return_value = {"id": 11111}

        # Create custom configuration
        custom_config = ResolutionRequestConfig(
            resolved_marker="✅ CUSTOM_RESOLVED ✅",
            request_template="@coderabbitai Custom request: please verify and mark as {marker}",
            custom_prefix="🔍 Code Review Request",
            custom_suffix="Generated by automated system",
            include_context=True
        )

        poster = CommentPoster(mock_github_client, custom_config)

        # Test message generation with custom config
        pr_url = "https://github.com/custom/repo/pull/999"
        context = "Authentication module refactoring complete"

        result = poster.post_resolution_request(pr_url, context)

        # Verify custom elements are present
        message = result["message"]
        assert "🔍 Code Review Request" in message
        assert "✅ CUSTOM_RESOLVED ✅" in message
        assert "Custom request: please verify" in message
        assert "Generated by automated system" in message
        assert "Authentication module refactoring" in message

        # Test dynamic configuration updates
        poster.update_config(
            resolved_marker="🔐 UPDATED_MARKER 🔐",
            include_context=False
        )

        result2 = poster.post_resolution_request(pr_url, "This context should be ignored")

        # Verify updates were applied
        message2 = result2["message"]
        assert "🔐 UPDATED_MARKER 🔐" in message2
        assert "This context should be ignored" not in message2

        # Verify statistics reflect changes
        stats = poster.get_posting_statistics()
        assert stats["resolved_marker"] == "🔐 UPDATED_MARKER 🔐"
        assert stats["config_valid"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Unit tests for validation utilities."""

import unittest
import tempfile
import os
from pathlib import Path

from coderabbit_fetcher.validation import (
    URLValidator,
    FileValidator,
    OptionsValidator,
    ValidationSuite,
    ValidationResult
)


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult class."""

    def test_validation_result_creation(self):
        """Test ValidationResult creation and basic operations."""
        result = ValidationResult(valid=True)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.issues), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertEqual(len(result.suggestions), 0)

    def test_add_issue(self):
        """Test adding issues invalidates result."""
        result = ValidationResult(valid=True)
        result.add_issue("Test issue")

        self.assertFalse(result.valid)
        self.assertIn("Test issue", result.issues)

    def test_add_warning(self):
        """Test adding warnings doesn't invalidate result."""
        result = ValidationResult(valid=True)
        result.add_warning("Test warning")

        self.assertTrue(result.valid)
        self.assertIn("Test warning", result.warnings)

    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult(valid=True)
        result1.add_warning("Warning 1")

        result2 = ValidationResult(valid=False)
        result2.add_issue("Issue 1")
        result2.add_suggestion("Suggestion 1")

        result1.merge(result2)

        self.assertFalse(result1.valid)
        self.assertIn("Warning 1", result1.warnings)
        self.assertIn("Issue 1", result1.issues)
        self.assertIn("Suggestion 1", result1.suggestions)


class TestURLValidator(unittest.TestCase):
    """Test URL validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = URLValidator()

    def test_valid_github_pr_url(self):
        """Test validation of valid GitHub PR URLs."""
        valid_urls = [
            "https://github.com/owner/repo/pull/123",
            "https://github.com/test-user/test-repo/pull/1",
            "https://github.com/org_name/repo.name/pull/999999"
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                result = self.validator.validate_pr_url(url)
                self.assertTrue(result.valid, f"URL should be valid: {url}")
                self.assertIn("owner", result.details)
                self.assertIn("repo", result.details)
                self.assertIn("pr_number", result.details)

    def test_invalid_github_pr_urls(self):
        """Test validation of invalid GitHub PR URLs."""
        invalid_urls = [
            "",  # Empty
            "not-a-url",  # Not a URL
            "http://example.com",  # Wrong domain
            "https://github.com/owner",  # Incomplete
            "https://github.com/owner/repo",  # Missing pull path
            "https://github.com/owner/repo/issues/123",  # Wrong path type
            "https://github.com/owner/repo/pull/abc",  # Invalid PR number
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                result = self.validator.validate_pr_url(url)
                self.assertFalse(result.valid, f"URL should be invalid: {url}")
                self.assertGreater(len(result.issues), 0)

    def test_http_to_https_correction(self):
        """Test automatic HTTP to HTTPS correction."""
        result = self.validator.validate_pr_url("http://github.com/owner/repo/pull/123")

        self.assertTrue(result.valid)
        self.assertGreater(len(result.warnings), 0)
        self.assertIn("HTTPS", result.warnings[0])

    def test_github_identifier_validation(self):
        """Test GitHub owner/repo identifier validation."""
        # Valid identifiers
        valid_cases = ["user", "test-user", "org_name", "repo.name", "123test"]
        for identifier in valid_cases:
            result = self.validator._validate_github_identifier(identifier, "test")
            self.assertTrue(result.valid, f"Should be valid: {identifier}")

        # Invalid identifiers
        invalid_cases = [
            "",  # Empty
            ".start",  # Starts with dot
            "end-",  # Ends with dash
            "a" * 40,  # Too long
            "test@user",  # Invalid character
        ]
        for identifier in invalid_cases:
            result = self.validator._validate_github_identifier(identifier, "test")
            self.assertFalse(result.valid, f"Should be invalid: {identifier}")

    def test_pr_number_validation(self):
        """Test pull request number validation."""
        # Valid numbers
        valid_numbers = ["1", "123", "999999"]
        for number in valid_numbers:
            result = self.validator._validate_pr_number(number)
            self.assertTrue(result.valid, f"Should be valid: {number}")

        # Invalid numbers
        invalid_numbers = ["0", "-1", "abc", "12.5"]
        for number in invalid_numbers:
            result = self.validator._validate_pr_number(number)
            self.assertFalse(result.valid, f"Should be invalid: {number}")


class TestFileValidator(unittest.TestCase):
    """Test file validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FileValidator()

    def test_validate_existing_persona_file(self):
        """Test validation of existing persona file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test persona content")
            temp_file = f.name

        try:
            result = self.validator.validate_persona_file(temp_file)
            self.assertTrue(result.valid)
            self.assertIn("file_size", result.details)
            self.assertGreater(result.details["file_size"], 0)
        finally:
            os.unlink(temp_file)

    def test_validate_nonexistent_persona_file(self):
        """Test validation of non-existent persona file."""
        result = self.validator.validate_persona_file("/nonexistent/file.txt")

        self.assertFalse(result.valid)
        self.assertGreater(len(result.issues), 0)
        self.assertIn("does not exist", result.issues[0])

    def test_validate_empty_persona_file(self):
        """Test validation of empty persona file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Create empty file
            temp_file = f.name

        try:
            result = self.validator.validate_persona_file(temp_file)
            self.assertTrue(result.valid)  # Empty file is valid but warns
            self.assertGreater(len(result.warnings), 0)
            self.assertIn("empty", result.warnings[0])
        finally:
            os.unlink(temp_file)

    def test_validate_binary_file(self):
        """Test validation of binary file."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            f.write(b'\x00\x01\x02\x03')  # Binary content
            temp_file = f.name

        try:
            result = self.validator.validate_persona_file(temp_file)
            self.assertFalse(result.valid)
            self.assertIn("binary", result.issues[0])
        finally:
            os.unlink(temp_file)

    def test_validate_output_path_creation(self):
        """Test output path validation with directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "subdir", "output.txt")

            result = self.validator.validate_output_path(output_path)

            self.assertTrue(result.valid)
            self.assertTrue(os.path.exists(os.path.dirname(output_path)))
            self.assertIn("resolved_path", result.details)

    def test_validate_output_path_existing_file(self):
        """Test output path validation with existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            result = self.validator.validate_output_path(temp_file)
            self.assertTrue(result.valid)
            self.assertGreater(len(result.warnings), 0)
            self.assertIn("overwritten", result.warnings[0])
        finally:
            os.unlink(temp_file)


class TestOptionsValidator(unittest.TestCase):
    """Test options validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = OptionsValidator()

    def test_validate_output_format(self):
        """Test output format validation."""
        # Valid formats
        valid_formats = ['markdown', 'json', 'plain']
        for fmt in valid_formats:
            result = self.validator.validate_output_format(fmt)
            self.assertTrue(result.valid, f"Format should be valid: {fmt}")

        # Invalid formats
        invalid_formats = ['', 'xml', 'html', 'pdf']
        for fmt in invalid_formats:
            result = self.validator.validate_output_format(fmt)
            self.assertFalse(result.valid, f"Format should be invalid: {fmt}")

    def test_validate_timeout(self):
        """Test timeout validation."""
        # Valid timeouts
        valid_timeouts = [10, 30.5, "60", 120]
        for timeout in valid_timeouts:
            result = self.validator.validate_timeout(timeout)
            self.assertTrue(result.valid, f"Timeout should be valid: {timeout}")

        # Invalid timeouts
        invalid_timeouts = [0, -5, "abc", None]
        for timeout in invalid_timeouts:
            result = self.validator.validate_timeout(timeout)
            self.assertFalse(result.valid, f"Timeout should be invalid: {timeout}")

        # Short timeout (warning)
        result = self.validator.validate_timeout(3)
        self.assertTrue(result.valid)
        self.assertGreater(len(result.warnings), 0)

    def test_validate_retry_settings(self):
        """Test retry settings validation."""
        # Valid settings
        result = self.validator.validate_retry_settings(3, 1.5)
        self.assertTrue(result.valid)
        self.assertEqual(result.details["retry_attempts"], 3)
        self.assertEqual(result.details["retry_delay"], 1.5)

        # Invalid attempts
        result = self.validator.validate_retry_settings(-1, 1.0)
        self.assertFalse(result.valid)

        # Invalid delay
        result = self.validator.validate_retry_settings(3, -0.5)
        self.assertFalse(result.valid)

    def test_validate_resolved_marker(self):
        """Test resolved marker validation."""
        # Good marker
        result = self.validator.validate_resolved_marker("🔒 RESOLVED 🔒")
        self.assertTrue(result.valid)
        self.assertGreater(result.details["special_char_count"], 0)

        # Short marker (warning)
        result = self.validator.validate_resolved_marker("ok")
        self.assertTrue(result.valid)
        self.assertGreater(len(result.warnings), 0)

        # Empty marker
        result = self.validator.validate_resolved_marker("")
        self.assertFalse(result.valid)

        # Marker with common words (warning)
        result = self.validator.validate_resolved_marker("resolved and done")
        self.assertTrue(result.valid)
        self.assertGreater(len(result.warnings), 0)


class TestValidationSuite(unittest.TestCase):
    """Test comprehensive validation suite."""

    def setUp(self):
        """Set up test fixtures."""
        self.suite = ValidationSuite()

    def test_validate_all_inputs_valid(self):
        """Test validation of all valid inputs."""
        config = {
            'pr_url': 'https://github.com/owner/repo/pull/123',
            'output_format': 'markdown',
            'timeout_seconds': 30,
            'retry_attempts': 3,
            'retry_delay': 1.0,
            'resolved_marker': '🔒 RESOLVED 🔒'
        }

        result = self.suite.validate_all_inputs(config)
        self.assertTrue(result.valid)

    def test_validate_all_inputs_invalid(self):
        """Test validation with invalid inputs."""
        config = {
            'pr_url': 'invalid-url',
            'output_format': 'invalid',
            'timeout_seconds': -1,
            'retry_attempts': -1,
            'retry_delay': -1,
            'resolved_marker': ''
        }

        result = self.suite.validate_all_inputs(config)
        self.assertFalse(result.valid)
        self.assertGreater(len(result.issues), 0)

    def test_validate_with_persona_file(self):
        """Test validation with persona file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test persona")
            temp_file = f.name

        try:
            config = {
                'pr_url': 'https://github.com/owner/repo/pull/123',
                'persona_file': temp_file
            }

            result = self.suite.validate_all_inputs(config)
            self.assertTrue(result.valid)
        finally:
            os.unlink(temp_file)

    def test_validation_report_generation(self):
        """Test validation report generation."""
        result = ValidationResult(valid=False)
        result.add_issue("Test issue")
        result.add_warning("Test warning")
        result.add_suggestion("Test suggestion")
        result.details = {"test_key": "test_value"}

        report = self.suite.generate_validation_report(result)

        self.assertIn("Configuration validation failed", report)
        self.assertIn("Test issue", report)
        self.assertIn("Test warning", report)
        self.assertIn("Test suggestion", report)
        self.assertIn("test_key", report)


if __name__ == '__main__':
    unittest.main()

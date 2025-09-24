"""Integration tests for the main orchestrator."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coderabbit_fetcher.exceptions import GitHubAuthenticationError, InvalidPRUrlError
from coderabbit_fetcher.orchestrator import CodeRabbitOrchestrator, ExecutionConfig


class TestOrchestratorIntegration(unittest.TestCase):
    """Integration tests for CodeRabbitOrchestrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = ExecutionConfig(
            pr_url="https://github.com/test/repo/pull/123",
            output_format="json",
            resolved_marker="🔒 TEST_RESOLVED 🔒",
        )

        # Sample PR data
        self.sample_pr_data = {
            "number": 123,
            "title": "Test PR",
            "url": "https://github.com/test/repo/pull/123",
            "comments": [
                {
                    "id": 1,
                    "body": "This is a test comment from CodeRabbit",
                    "user": {"login": "coderabbitai[bot]"},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
            "reviews": [
                {
                    "id": 2,
                    "body": "## Summary by CodeRabbit\n\nTest summary",
                    "user": {"login": "coderabbitai[bot]"},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
        }

    def test_configuration_validation_valid(self):
        """Test valid configuration validation."""
        orchestrator = CodeRabbitOrchestrator(self.config)
        result = orchestrator.validate_configuration()

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["issues"]), 0)

    def test_configuration_validation_invalid_url(self):
        """Test invalid URL configuration validation."""
        invalid_config = ExecutionConfig(pr_url="invalid-url")
        orchestrator = CodeRabbitOrchestrator(invalid_config)
        result = orchestrator.validate_configuration()

        self.assertFalse(result["valid"])
        self.assertGreater(len(result["issues"]), 0)
        self.assertIn("valid HTTP/HTTPS URL", str(result["issues"]))

    def test_configuration_validation_invalid_format(self):
        """Test invalid output format configuration validation."""
        invalid_config = ExecutionConfig(
            pr_url="https://github.com/test/repo/pull/123", output_format="invalid"
        )
        orchestrator = CodeRabbitOrchestrator(invalid_config)
        result = orchestrator.validate_configuration()

        self.assertFalse(result["valid"])
        self.assertIn("Invalid output format", str(result["issues"]))

    def test_configuration_validation_missing_persona_file(self):
        """Test missing persona file configuration validation."""
        invalid_config = ExecutionConfig(
            pr_url="https://github.com/test/repo/pull/123", persona_file="/nonexistent/file.txt"
        )
        orchestrator = CodeRabbitOrchestrator(invalid_config)
        result = orchestrator.validate_configuration()

        self.assertFalse(result["valid"])
        self.assertIn("Persona file not found", str(result["issues"]))

    @patch("coderabbit_fetcher.orchestrator.GitHubClient")
    @patch("coderabbit_fetcher.orchestrator.PersonaManager")
    @patch("coderabbit_fetcher.orchestrator.CommentAnalyzer")
    def test_successful_execution_with_mocks(self, mock_analyzer, mock_persona, mock_github):
        """Test successful execution with all components mocked."""
        # Setup mocks
        mock_github_instance = Mock()
        mock_github_instance.parse_pr_url.return_value = ("test", "repo", "123")
        mock_github_instance.fetch_pr_comments.return_value = self.sample_pr_data
        mock_github.return_value = mock_github_instance

        mock_persona_instance = Mock()
        # Mock all persona manager methods that orchestrator uses
        mock_persona_instance.get_default_persona.return_value = "Test persona content that is long enough to pass validation checks and provide meaningful analysis for the code review process"
        mock_persona_instance.load_from_file.return_value = "Test persona content that is long enough to pass validation checks and provide meaningful analysis for the code review process"
        mock_persona_instance.load_persona.return_value = "Test persona content that is long enough to pass validation checks and provide meaningful analysis for the code review process"
        mock_persona.return_value = mock_persona_instance

        # Mock analyzed comments
        mock_analyzed_comments = Mock()
        mock_analyzed_comments.metadata = Mock()
        mock_analyzed_comments.metadata.total_comments = 2
        mock_analyzed_comments.metadata.coderabbit_comments = 2
        mock_analyzed_comments.metadata.actionable_comments = 1
        mock_analyzed_comments.unresolved_threads = []

        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze_comments.return_value = mock_analyzed_comments
        mock_analyzer.return_value = mock_analyzer_instance

        # Execute
        orchestrator = CodeRabbitOrchestrator(self.config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            orchestrator.config.output_file = f.name

        try:
            results = orchestrator.execute()

            # Verify success
            self.assertTrue(results["success"])
            self.assertIn("pr_info", results)
            self.assertIn("analyzed_comments", results)
            self.assertIn("metrics", results)

            # Verify metrics
            metrics = results["metrics"]
            self.assertGreater(metrics["execution_time"], 0)
            self.assertEqual(metrics["github_api_calls"], 2)  # Auth check + fetch
            self.assertEqual(metrics["total_comments_processed"], 2)

            # Verify output file was created
            output_path = Path(orchestrator.config.output_file)
            self.assertTrue(output_path.exists())

            # Verify output content
            with open(output_path) as f:
                content = f.read()
                self.assertGreater(len(content), 0)

        finally:
            # Cleanup
            output_path = Path(orchestrator.config.output_file)
            if output_path.exists():
                output_path.unlink()

    @patch("coderabbit_fetcher.orchestrator.GitHubClient")
    def test_github_authentication_failure(self, mock_github):
        """Test handling of GitHub authentication failure."""
        # Setup mock to raise authentication error
        mock_github.side_effect = GitHubAuthenticationError("Authentication required")

        orchestrator = CodeRabbitOrchestrator(self.config)
        results = orchestrator.execute()

        # Verify failure handling
        self.assertFalse(results["success"])
        self.assertEqual(results["error_type"], "GitHubAuthenticationError")
        self.assertIn("recovery_info", results)
        self.assertIn("recommendations", results["recovery_info"])

    @patch("coderabbit_fetcher.orchestrator.GitHubClient")
    def test_invalid_pr_url_failure(self, mock_github):
        """Test handling of invalid PR URL."""
        mock_github_instance = Mock()
        mock_github_instance.parse_pr_url.side_effect = InvalidPRUrlError("Invalid URL format")
        mock_github.return_value = mock_github_instance

        orchestrator = CodeRabbitOrchestrator(self.config)
        results = orchestrator.execute()

        # Verify failure handling
        self.assertFalse(results["success"])
        self.assertEqual(results["error_type"], "InvalidPRUrlError")
        self.assertIn("recovery_info", results)
        self.assertIn("recommendations", results["recovery_info"])

    def test_progress_tracking(self):
        """Test progress tracking functionality."""
        orchestrator = CodeRabbitOrchestrator(self.config)

        # Initial state
        progress = orchestrator.get_progress_info()
        self.assertEqual(progress["current_step"], 0)
        self.assertEqual(progress["percentage"], 0)
        self.assertFalse(progress["is_complete"])

        # Advance progress
        orchestrator.progress_tracker.advance("Test step")
        progress = orchestrator.get_progress_info()
        self.assertEqual(progress["current_step"], 1)
        self.assertGreater(progress["percentage"], 0)

        # Complete progress
        orchestrator.progress_tracker.complete()
        progress = orchestrator.get_progress_info()
        self.assertTrue(progress["is_complete"])

    def test_metrics_collection(self):
        """Test metrics collection during execution."""
        orchestrator = CodeRabbitOrchestrator(self.config)

        # Check initial metrics
        metrics = orchestrator.get_detailed_metrics()
        self.assertEqual(metrics.github_api_calls, 0)
        self.assertEqual(metrics.total_comments_processed, 0)

        # Simulate some metrics updates
        orchestrator.metrics.github_api_calls = 3
        orchestrator.metrics.total_comments_processed = 15
        orchestrator.metrics.coderabbit_comments_found = 8
        orchestrator.metrics.resolved_comments_filtered = 2

        # Check metrics summary
        summary = orchestrator._get_metrics_summary()
        self.assertEqual(summary["github_api_calls"], 3)
        self.assertEqual(summary["total_comments_processed"], 15)
        self.assertEqual(summary["coderabbit_comments_found"], 8)
        self.assertEqual(summary["resolved_comments_filtered"], 2)

    def test_persona_file_handling(self):
        """Test persona file handling."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Custom test persona for AI agent")
            persona_file = f.name

        try:
            config = ExecutionConfig(
                pr_url="https://github.com/test/repo/pull/123", persona_file=persona_file
            )
            orchestrator = CodeRabbitOrchestrator(config)

            # Validate configuration should pass
            result = orchestrator.validate_configuration()
            self.assertTrue(result["valid"])

        finally:
            Path(persona_file).unlink()

    def test_output_file_directory_creation(self):
        """Test automatic output directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "subdir" / "output.json"

            config = ExecutionConfig(
                pr_url="https://github.com/test/repo/pull/123", output_file=str(output_file)
            )
            orchestrator = CodeRabbitOrchestrator(config)

            # Directory should be created during validation
            result = orchestrator.validate_configuration()
            self.assertTrue(result["valid"])
            self.assertTrue(output_file.parent.exists())

    def test_retry_configuration_validation(self):
        """Test retry configuration validation."""
        # Valid retry settings
        config = ExecutionConfig(
            pr_url="https://github.com/test/repo/pull/123", retry_attempts=3, retry_delay=1.0
        )
        orchestrator = CodeRabbitOrchestrator(config)
        result = orchestrator.validate_configuration()
        self.assertTrue(result["valid"])

        # Invalid retry attempts
        invalid_config = ExecutionConfig(
            pr_url="https://github.com/test/repo/pull/123", retry_attempts=-1
        )
        orchestrator = CodeRabbitOrchestrator(invalid_config)
        result = orchestrator.validate_configuration()
        self.assertFalse(result["valid"])
        self.assertIn("Retry attempts cannot be negative", str(result["issues"]))

    def test_timeout_configuration_validation(self):
        """Test timeout configuration validation."""
        # Valid timeout
        config = ExecutionConfig(
            pr_url="https://github.com/test/repo/pull/123", timeout_seconds=120
        )
        orchestrator = CodeRabbitOrchestrator(config)
        result = orchestrator.validate_configuration()
        self.assertTrue(result["valid"])

        # Invalid timeout
        invalid_config = ExecutionConfig(
            pr_url="https://github.com/test/repo/pull/123", timeout_seconds=0
        )
        orchestrator = CodeRabbitOrchestrator(invalid_config)
        result = orchestrator.validate_configuration()
        self.assertFalse(result["valid"])
        self.assertIn("Timeout must be positive", str(result["issues"]))

        # Very short timeout (warning)
        warning_config = ExecutionConfig(
            pr_url="https://github.com/test/repo/pull/123", timeout_seconds=15
        )
        orchestrator = CodeRabbitOrchestrator(warning_config)
        result = orchestrator.validate_configuration()
        self.assertTrue(result["valid"])
        self.assertGreater(len(result["warnings"]), 0)
        self.assertIn("very short", str(result["warnings"]))


if __name__ == "__main__":
    unittest.main()

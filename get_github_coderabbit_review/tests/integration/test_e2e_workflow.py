"""End-to-end workflow tests for CodeRabbit Comment Fetcher."""

import unittest
import tempfile
import os
import shutil
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from coderabbit_fetcher.orchestrator import CodeRabbitOrchestrator, ExecutionConfig
from coderabbit_fetcher.exceptions import (
    ValidationError,
    GitHubAuthenticationError,
    InvalidPRUrlError,
    TransientError,
)
from tests.fixtures.sample_data import (
    SAMPLE_PR_DATA,
    SAMPLE_CODERABBIT_COMMENTS,
    SAMPLE_LARGE_DATASET,
)
from tests.fixtures.github_responses import (
    MOCK_GH_PR_RESPONSE,
    MOCK_GH_COMMENTS_RESPONSE,
    MOCK_SUCCESS_RESPONSES,
)
from tests.fixtures.persona_files import PersonaFileManager, PERSONA_FILE_CONTENT


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflow scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix="e2e_test_")
        self.persona_manager = PersonaFileManager()

        # Create sample persona file
        self.persona_file = self.persona_manager.create_temp_persona_file(
            {
                "content": PERSONA_FILE_CONTENT["default"],
                "filename": "test_persona.txt",
                "encoding": "utf-8",
            }
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.persona_manager.cleanup()

        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.unlink(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_complete_successful_workflow(self, mock_validate, mock_auth, mock_fetch):
        """Test complete successful workflow from start to finish."""
        # Mock GitHub client responses
        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": MOCK_GH_PR_RESPONSE,
            "comments": MOCK_GH_COMMENTS_RESPONSE,
        }

        # Create configuration
        output_file = os.path.join(self.temp_dir, "output.md")
        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/123",
            persona_file=self.persona_file,
            output_format="markdown",
            output_file=output_file,
            show_stats=True,
            debug=False,
        )

        # Execute workflow
        orchestrator = CodeRabbitOrchestrator(config)
        results = orchestrator.execute()

        # Verify results
        self.assertTrue(results["success"])
        self.assertIn("metrics", results)
        self.assertGreater(results["execution_time"], 0)

        # Verify output file was created
        self.assertTrue(os.path.exists(output_file))

        # Verify output content
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("CodeRabbit", content)
            self.assertIn("Comments Analysis", content)

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_workflow_with_different_output_formats(self, mock_validate, mock_auth, mock_fetch):
        """Test workflow with different output formats."""
        # Mock GitHub client responses
        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": MOCK_GH_PR_RESPONSE,
            "comments": MOCK_GH_COMMENTS_RESPONSE,
        }

        formats = ["markdown", "json", "plain"]

        for output_format in formats:
            with self.subTest(format=output_format):
                output_file = os.path.join(self.temp_dir, f"output.{output_format}")
                config = ExecutionConfig(
                    pr_url="https://github.com/owner/repo/pull/123",
                    output_format=output_format,
                    output_file=output_file,
                )

                orchestrator = CodeRabbitOrchestrator(config)
                results = orchestrator.execute()

                self.assertTrue(results["success"])
                self.assertTrue(os.path.exists(output_file))

                # Verify format-specific content
                with open(output_file, "r", encoding="utf-8") as f:
                    content = f.read()

                    if output_format == "json":
                        # Should be valid JSON
                        json.loads(content)
                    elif output_format == "markdown":
                        self.assertIn("#", content)  # Should have headers
                    elif output_format == "plain":
                        self.assertIsInstance(content, str)

    def test_workflow_validation_failure(self):
        """Test workflow with validation failures."""
        # Invalid URL
        config = ExecutionConfig(pr_url="invalid-url", output_format="markdown")

        orchestrator = CodeRabbitOrchestrator(config)

        # Validation should fail
        validation_result = orchestrator.validate_configuration()
        self.assertFalse(validation_result["valid"])
        self.assertGreater(len(validation_result["issues"]), 0)

    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    def test_workflow_authentication_failure(self, mock_auth):
        """Test workflow with authentication failure."""
        mock_auth.side_effect = GitHubAuthenticationError("Authentication required")

        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/123", output_format="markdown"
        )

        orchestrator = CodeRabbitOrchestrator(config)
        results = orchestrator.execute()

        self.assertFalse(results["success"])
        self.assertIn("error", results)
        self.assertIn("authentication", results["error"].lower())

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_workflow_with_resolved_marker_filtering(self, mock_validate, mock_auth, mock_fetch):
        """Test workflow with resolved marker filtering."""
        # Mock responses including resolved comments
        from tests.fixtures.sample_data import SAMPLE_RESOLVED_COMMENTS

        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": MOCK_GH_PR_RESPONSE,
            "comments": MOCK_GH_COMMENTS_RESPONSE + SAMPLE_RESOLVED_COMMENTS,
        }

        output_file = os.path.join(self.temp_dir, "output_filtered.md")
        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/123",
            output_format="markdown",
            output_file=output_file,
            resolved_marker="🔒 CODERABBIT_RESOLVED 🔒",
        )

        orchestrator = CodeRabbitOrchestrator(config)
        results = orchestrator.execute()

        self.assertTrue(results["success"])
        self.assertTrue(os.path.exists(output_file))

        # Verify metrics include filtering information
        metrics = results["metrics"]
        self.assertIn("comments_processed", metrics)
        self.assertIn("resolved_comments_filtered", metrics)

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_workflow_with_comment_posting(self, mock_validate, mock_auth, mock_fetch):
        """Test workflow with comment posting enabled."""
        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": MOCK_GH_PR_RESPONSE,
            "comments": MOCK_GH_COMMENTS_RESPONSE,
        }

        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/123",
            output_format="markdown",
            post_resolution_request=True,
        )

        # Mock comment posting
        with patch("coderabbit_fetcher.github_client.GitHubClient.post_comment") as mock_post:
            mock_post.return_value = {"id": 12345, "body": "Resolution request posted"}

            orchestrator = CodeRabbitOrchestrator(config)
            results = orchestrator.execute()

            self.assertTrue(results["success"])

            # Verify comment posting was attempted
            mock_post.assert_called()

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_workflow_error_recovery(self, mock_validate, mock_auth, mock_fetch):
        """Test workflow error recovery mechanisms."""
        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True

        # Simulate transient error followed by success
        call_count = 0

        def mock_fetch_with_retry(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TransientError("Temporary network issue")
            return {"pr_data": MOCK_GH_PR_RESPONSE, "comments": MOCK_GH_COMMENTS_RESPONSE}

        mock_fetch.side_effect = mock_fetch_with_retry

        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/123",
            output_format="markdown",
            retry_attempts=3,
            retry_delay=0.1,  # Short delay for testing
        )

        orchestrator = CodeRabbitOrchestrator(config)
        results = orchestrator.execute()

        # Should succeed after retry
        self.assertTrue(results["success"])
        self.assertEqual(call_count, 2)  # One failure, one success

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_workflow_with_japanese_persona(self, mock_validate, mock_auth, mock_fetch):
        """Test workflow with Japanese persona file."""
        # Create Japanese persona file
        japanese_persona = self.persona_manager.create_temp_persona_file(
            {
                "content": PERSONA_FILE_CONTENT["japanese_reviewer"],
                "filename": "japanese_persona.txt",
                "encoding": "utf-8",
            }
        )

        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": MOCK_GH_PR_RESPONSE,
            "comments": MOCK_GH_COMMENTS_RESPONSE,
        }

        output_file = os.path.join(self.temp_dir, "output_japanese.md")
        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/123",
            persona_file=japanese_persona,
            output_format="markdown",
            output_file=output_file,
        )

        orchestrator = CodeRabbitOrchestrator(config)
        results = orchestrator.execute()

        self.assertTrue(results["success"])
        self.assertTrue(os.path.exists(output_file))

        # Verify Japanese content is preserved
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("日本語", content.lower())


class TestPerformanceWorkflow(unittest.TestCase):
    """Test performance aspects of the workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix="perf_test_")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.unlink(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_large_dataset_performance(self, mock_validate, mock_auth, mock_fetch):
        """Test performance with large comment datasets."""
        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": SAMPLE_LARGE_DATASET["metadata"],
            "comments": SAMPLE_LARGE_DATASET["inline_comments"],
        }

        output_file = os.path.join(self.temp_dir, "large_output.json")
        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/999",
            output_format="json",
            output_file=output_file,
            timeout_seconds=60,  # Longer timeout for large dataset
        )

        import time

        start_time = time.time()

        orchestrator = CodeRabbitOrchestrator(config)
        results = orchestrator.execute()

        execution_time = time.time() - start_time

        # Performance assertions
        self.assertTrue(results["success"])
        self.assertLess(execution_time, 30)  # Should complete within 30 seconds

        # Verify large dataset was processed
        metrics = results["metrics"]
        self.assertGreaterEqual(metrics["comments_processed"], 500)

        # Verify output file size is reasonable
        self.assertTrue(os.path.exists(output_file))
        file_size = os.path.getsize(output_file)
        self.assertGreater(file_size, 1000)  # Should have substantial content
        self.assertLess(file_size, 10 * 1024 * 1024)  # But not excessive (< 10MB)

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_memory_usage_with_large_dataset(self, mock_validate, mock_auth, mock_fetch):
        """Test memory usage with large comment datasets."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": SAMPLE_LARGE_DATASET["metadata"],
            "comments": SAMPLE_LARGE_DATASET["inline_comments"],
        }

        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/999", output_format="json"
        )

        orchestrator = CodeRabbitOrchestrator(config)
        results = orchestrator.execute()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory usage should be reasonable (< 100MB increase)
        self.assertTrue(results["success"])
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # < 100MB

    @patch("coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments")
    @patch("coderabbit_fetcher.github_client.GitHubClient.check_authentication")
    @patch("coderabbit_fetcher.github_client.GitHubClient.validate")
    def test_concurrent_workflow_execution(self, mock_validate, mock_auth, mock_fetch):
        """Test concurrent execution of workflows."""
        import threading
        import time

        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": MOCK_GH_PR_RESPONSE,
            "comments": MOCK_GH_COMMENTS_RESPONSE,
        }

        results = []
        errors = []

        def run_workflow(index):
            try:
                output_file = os.path.join(self.temp_dir, f"concurrent_output_{index}.md")
                config = ExecutionConfig(
                    pr_url=f"https://github.com/owner/repo/pull/{100 + index}",
                    output_format="markdown",
                    output_file=output_file,
                )

                orchestrator = CodeRabbitOrchestrator(config)
                result = orchestrator.execute()
                results.append((index, result))
            except (ValidationError, GitHubAuthenticationError, IOError, RuntimeError) as e:
                errors.append((index, e))

        # Start multiple concurrent workflows
        threads = []
        num_threads = 3

        start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(target=run_workflow, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        execution_time = time.time() - start_time

        # Verify results
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
        self.assertEqual(len(results), num_threads)

        for index, result in results:
            self.assertTrue(result["success"], f"Workflow {index} failed")

        # Concurrent execution should not take much longer than sequential
        self.assertLess(execution_time, 15)  # Should complete within 15 seconds


class TestUvxCompatibility(unittest.TestCase):
    """Test uvx execution compatibility."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix="uvx_test_")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.unlink(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)

    @unittest.skipIf(shutil.which("uvx") is None, "uvx not available")
    def test_uvx_execution_compatibility(self):
        """Test that the package can be executed via uvx."""
        # This is a basic test that would require actual package installation
        # In a real scenario, this would test:
        # 1. uvx package installation
        # 2. Entry point execution
        # 3. CLI argument handling
        # 4. Output generation

        # For now, we'll test the entry point structure
        from coderabbit_fetcher.cli.main import main

        # Verify the main function exists and is callable
        self.assertTrue(callable(main))

    def test_package_structure_for_uvx(self):
        """Test that package structure is compatible with uvx."""
        import coderabbit_fetcher

        # Verify package has necessary components
        self.assertTrue(hasattr(coderabbit_fetcher, "__version__"))

        # Verify CLI module exists
        from coderabbit_fetcher.cli import main

        self.assertTrue(hasattr(main, "main"))

    def test_dependency_compatibility(self):
        """Test that dependencies are compatible with uvx."""
        # Test that all required modules can be imported
        required_modules = [
            "argparse",  # Standard library
            "json",  # Standard library
            "pathlib",  # Standard library
            "subprocess",  # Standard library
        ]

        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError:
                self.fail(f"Required module {module_name} cannot be imported")


if __name__ == "__main__":
    unittest.main()

"""Performance tests for CodeRabbit Comment Fetcher."""

import unittest
import time
import tempfile
import os
import json
import psutil
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

from coderabbit_fetcher.orchestrator import CodeRabbitOrchestrator, ExecutionConfig
from coderabbit_fetcher.comment_analyzer import CommentAnalyzer
from coderabbit_fetcher.formatters.markdown import MarkdownFormatter
from tests.fixtures.github_responses import generate_mock_comments
from tests.fixtures.sample_data import SAMPLE_LARGE_DATASET


class PerformanceTestBase(unittest.TestCase):
    """Base class for performance tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix="perf_test_")
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                try:
                    os.unlink(os.path.join(self.temp_dir, file))
                except:
                    pass
            try:
                os.rmdir(self.temp_dir)
            except:
                pass
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (result, execution_time_seconds)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (result, memory_increase_bytes)
        """
        initial_memory = self.process.memory_info().rss
        result = func(*args, **kwargs)
        final_memory = self.process.memory_info().rss
        return result, final_memory - initial_memory
    
    def generate_large_comment_dataset(self, size: int) -> List[Dict[str, Any]]:
        """Generate large comment dataset for testing.
        
        Args:
            size: Number of comments to generate
            
        Returns:
            List of mock comments
        """
        return generate_mock_comments(size, "coderabbit")


class TestCommentAnalysisPerformance(PerformanceTestBase):
    """Test performance of comment analysis operations."""
    
    def test_analyze_small_dataset_performance(self):
        """Test analysis performance with small dataset (10 comments)."""
        comments = self.generate_large_comment_dataset(10)
        analyzer = CommentAnalyzer()
        
        result, execution_time = self.measure_execution_time(
            analyzer.analyze_comments, comments
        )
        
        # Small dataset should be very fast
        self.assertLess(execution_time, 1.0)  # < 1 second
        self.assertIsInstance(result, dict)
        self.assertIn("coderabbit_comments", result)
    
    def test_analyze_medium_dataset_performance(self):
        """Test analysis performance with medium dataset (100 comments)."""
        comments = self.generate_large_comment_dataset(100)
        analyzer = CommentAnalyzer()
        
        result, execution_time = self.measure_execution_time(
            analyzer.analyze_comments, comments
        )
        
        # Medium dataset should still be fast
        self.assertLess(execution_time, 5.0)  # < 5 seconds
        self.assertGreater(len(result["coderabbit_comments"]), 0)
    
    def test_analyze_large_dataset_performance(self):
        """Test analysis performance with large dataset (1000 comments)."""
        comments = self.generate_large_comment_dataset(1000)
        analyzer = CommentAnalyzer()
        
        result, execution_time = self.measure_execution_time(
            analyzer.analyze_comments, comments
        )
        
        # Large dataset should complete within reasonable time
        self.assertLess(execution_time, 15.0)  # < 15 seconds
        self.assertGreater(len(result["coderabbit_comments"]), 0)
    
    def test_analyze_very_large_dataset_performance(self):
        """Test analysis performance with very large dataset (5000 comments)."""
        comments = self.generate_large_comment_dataset(5000)
        analyzer = CommentAnalyzer()
        
        result, execution_time = self.measure_execution_time(
            analyzer.analyze_comments, comments
        )
        
        # Very large dataset should still be manageable
        self.assertLess(execution_time, 30.0)  # < 30 seconds
        
        # Verify result quality is maintained
        self.assertGreater(len(result["coderabbit_comments"]), 1000)
    
    def test_comment_analysis_memory_usage(self):
        """Test memory usage during comment analysis."""
        comments = self.generate_large_comment_dataset(1000)
        analyzer = CommentAnalyzer()
        
        result, memory_increase = self.measure_memory_usage(
            analyzer.analyze_comments, comments
        )
        
        # Memory usage should be reasonable (< 50MB for 1000 comments)
        self.assertLess(memory_increase, 50 * 1024 * 1024)  # < 50MB
        self.assertGreater(len(result["coderabbit_comments"]), 0)
    
    def test_thread_processing_performance(self):
        """Test performance of thread processing."""
        from tests.fixtures.sample_data import SAMPLE_THREAD_DATA
        
        # Generate threaded comments
        threaded_comments = []
        for i in range(100):
            base_comment = SAMPLE_THREAD_DATA[0].copy()
            base_comment["id"] = 1000000 + i
            threaded_comments.append(base_comment)
            
            # Add reply
            reply = SAMPLE_THREAD_DATA[1].copy()
            reply["id"] = 2000000 + i
            reply["in_reply_to_id"] = base_comment["id"]
            threaded_comments.append(reply)
        
        analyzer = CommentAnalyzer()
        
        result, execution_time = self.measure_execution_time(
            analyzer.analyze_comments, threaded_comments
        )
        
        # Thread processing should be efficient
        self.assertLess(execution_time, 10.0)  # < 10 seconds
        self.assertIn("threads", result)
    
    def test_resolved_marker_detection_performance(self):
        """Test performance of resolved marker detection."""
        from coderabbit_fetcher.resolved_marker import ResolvedMarkerManager, ResolvedMarkerConfig
        
        # Generate comments with and without resolved markers
        comments = []
        for i in range(1000):
            comment = {
                "id": i,
                "user": "coderabbitai[bot]",
                "body": f"Comment {i}" + (
                    "\n[CR_RESOLUTION_CONFIRMED:TECHNICAL_ISSUE_RESOLVED]\n✅ Resolved\n[/CR_RESOLUTION_CONFIRMED]"
                    if i % 3 == 0 else ""
                ),
                "is_coderabbit": True
            }
            comments.append(comment)
        
        config = ResolvedMarkerConfig()
        manager = ResolvedMarkerManager(config)
        
        result, execution_time = self.measure_execution_time(
            manager.filter_unresolved_comments, comments
        )
        
        # Resolved marker detection should be fast
        self.assertLess(execution_time, 5.0)  # < 5 seconds
        self.assertLess(len(result), len(comments))  # Some should be filtered


class TestFormattingPerformance(PerformanceTestBase):
    """Test performance of output formatting operations."""
    
    def test_markdown_formatting_performance(self):
        """Test markdown formatting performance."""
        from coderabbit_fetcher.models import AnalyzedComments
        
        # Generate analyzed comments
        comments = self.generate_large_comment_dataset(500)
        analyzed = AnalyzedComments(
            coderabbit_comments=comments,
            threads={},
            summary_comment=None,
            review_comments=[],
            metadata={"total_comments": len(comments)}
        )
        
        formatter = MarkdownFormatter()
        
        result, execution_time = self.measure_execution_time(
            formatter.format, analyzed, {}
        )
        
        # Formatting should be efficient
        self.assertLess(execution_time, 10.0)  # < 10 seconds
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 1000)  # Should have substantial content
    
    def test_json_formatting_performance(self):
        """Test JSON formatting performance."""
        from coderabbit_fetcher.formatters.json import JsonFormatter
        from coderabbit_fetcher.models import AnalyzedComments
        
        comments = self.generate_large_comment_dataset(500)
        analyzed = AnalyzedComments(
            coderabbit_comments=comments,
            threads={},
            summary_comment=None,
            review_comments=[],
            metadata={"total_comments": len(comments)}
        )
        
        formatter = JsonFormatter()
        
        result, execution_time = self.measure_execution_time(
            formatter.format, analyzed, {}
        )
        
        # JSON formatting should be very fast
        self.assertLess(execution_time, 5.0)  # < 5 seconds
        
        # Verify it's valid JSON
        json.loads(result)
    
    def test_large_content_formatting_memory(self):
        """Test memory usage during large content formatting."""
        from coderabbit_fetcher.formatters.markdown import MarkdownFormatter
        from coderabbit_fetcher.models import AnalyzedComments
        
        # Generate very large content
        large_comments = []
        for i in range(100):
            comment = {
                "id": i,
                "user": "coderabbitai[bot]",
                "body": "Large comment content. " * 1000,  # ~25KB per comment
                "created_at": "2025-08-27T17:00:00Z",
                "is_coderabbit": True
            }
            large_comments.append(comment)
        
        analyzed = AnalyzedComments(
            coderabbit_comments=large_comments,
            threads={},
            summary_comment=None,
            review_comments=[],
            metadata={"total_comments": len(large_comments)}
        )
        
        formatter = MarkdownFormatter()
        
        result, memory_increase = self.measure_memory_usage(
            formatter.format, analyzed, {}
        )
        
        # Memory usage should be reasonable even for large content
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # < 100MB
        self.assertGreater(len(result), 100000)  # Should have substantial content


class TestEndToEndPerformance(PerformanceTestBase):
    """Test end-to-end workflow performance."""
    
    @patch('coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments')
    @patch('coderabbit_fetcher.github_client.GitHubClient.check_authentication')
    @patch('coderabbit_fetcher.github_client.GitHubClient.validate')
    def test_complete_workflow_performance_small(self, mock_validate, mock_auth, mock_fetch):
        """Test complete workflow performance with small dataset."""
        # Mock responses
        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": {"number": 123, "title": "Test PR"},
            "comments": self.generate_large_comment_dataset(50)
        }
        
        output_file = os.path.join(self.temp_dir, "small_output.md")
        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/123",
            output_format="markdown",
            output_file=output_file
        )
        
        orchestrator = CodeRabbitOrchestrator(config)
        
        result, execution_time = self.measure_execution_time(
            orchestrator.execute
        )
        
        # Small workflow should be very fast
        self.assertLess(execution_time, 5.0)  # < 5 seconds
        self.assertTrue(result["success"])
    
    @patch('coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments')
    @patch('coderabbit_fetcher.github_client.GitHubClient.check_authentication')
    @patch('coderabbit_fetcher.github_client.GitHubClient.validate')
    def test_complete_workflow_performance_large(self, mock_validate, mock_auth, mock_fetch):
        """Test complete workflow performance with large dataset."""
        # Mock responses with large dataset
        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": {"number": 999, "title": "Large PR"},
            "comments": self.generate_large_comment_dataset(1000)
        }
        
        output_file = os.path.join(self.temp_dir, "large_output.json")
        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/999",
            output_format="json",
            output_file=output_file,
            timeout_seconds=60
        )
        
        orchestrator = CodeRabbitOrchestrator(config)
        
        result, execution_time = self.measure_execution_time(
            orchestrator.execute
        )
        
        # Large workflow should complete within reasonable time
        self.assertLess(execution_time, 30.0)  # < 30 seconds
        self.assertTrue(result["success"])
        
        # Verify substantial output was generated
        self.assertTrue(os.path.exists(output_file))
        file_size = os.path.getsize(output_file)
        self.assertGreater(file_size, 10000)  # > 10KB
    
    @patch('coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments')
    @patch('coderabbit_fetcher.github_client.GitHubClient.check_authentication')
    @patch('coderabbit_fetcher.github_client.GitHubClient.validate')
    def test_workflow_memory_efficiency(self, mock_validate, mock_auth, mock_fetch):
        """Test workflow memory efficiency."""
        mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
        mock_auth.return_value = True
        mock_fetch.return_value = {
            "pr_data": {"number": 500, "title": "Memory Test PR"},
            "comments": self.generate_large_comment_dataset(500)
        }
        
        config = ExecutionConfig(
            pr_url="https://github.com/owner/repo/pull/500",
            output_format="markdown"
        )
        
        orchestrator = CodeRabbitOrchestrator(config)
        
        result, memory_increase = self.measure_memory_usage(
            orchestrator.execute
        )
        
        # Memory usage should be reasonable
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # < 100MB
        self.assertTrue(result["success"])
    
    def test_concurrent_workflow_performance(self):
        """Test performance under concurrent execution."""
        import threading
        import time
        
        results = []
        execution_times = []
        
        def run_workflow():
            with patch('coderabbit_fetcher.github_client.GitHubClient.fetch_pr_comments') as mock_fetch, \
                 patch('coderabbit_fetcher.github_client.GitHubClient.check_authentication') as mock_auth, \
                 patch('coderabbit_fetcher.github_client.GitHubClient.validate') as mock_validate:
                
                mock_validate.return_value = {"valid": True, "issues": [], "warnings": []}
                mock_auth.return_value = True
                mock_fetch.return_value = {
                    "pr_data": {"number": 123, "title": "Concurrent Test"},
                    "comments": self.generate_large_comment_dataset(100)
                }
                
                config = ExecutionConfig(
                    pr_url="https://github.com/owner/repo/pull/123",
                    output_format="json"
                )
                
                orchestrator = CodeRabbitOrchestrator(config)
                
                start_time = time.time()
                result = orchestrator.execute()
                end_time = time.time()
                
                results.append(result)
                execution_times.append(end_time - start_time)
        
        # Run multiple concurrent workflows
        threads = []
        num_threads = 3
        
        overall_start = time.time()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=run_workflow)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        overall_end = time.time()
        overall_time = overall_end - overall_start
        
        # Verify all workflows succeeded
        self.assertEqual(len(results), num_threads)
        for result in results:
            self.assertTrue(result["success"])
        
        # Concurrent execution should not be much slower than sequential
        avg_execution_time = sum(execution_times) / len(execution_times)
        self.assertLess(overall_time, avg_execution_time * 2)  # At most 2x slower


class TestScalabilityLimits(PerformanceTestBase):
    """Test scalability limits and resource constraints."""
    
    def test_maximum_comment_processing(self):
        """Test processing at maximum reasonable comment count."""
        # Test with very large dataset (simulating real-world maximum)
        max_comments = 10000
        comments = self.generate_large_comment_dataset(max_comments)
        
        analyzer = CommentAnalyzer()
        
        start_time = time.time()
        try:
            result = analyzer.analyze_comments(comments)
            execution_time = time.time() - start_time
            
            # Should complete within reasonable time even for maximum dataset
            self.assertLess(execution_time, 60.0)  # < 1 minute
            self.assertGreater(len(result["coderabbit_comments"]), 1000)
            
        except MemoryError:
            self.skipTest("System does not have enough memory for maximum test")
        except Exception as e:
            self.fail(f"Unexpected error with maximum dataset: {e}")
    
    def test_memory_limit_handling(self):
        """Test handling of memory constraints."""
        # This test would ideally run in a memory-constrained environment
        # For now, we'll test with a reasonably large dataset
        large_dataset = []
        
        try:
            # Generate increasingly large comments until memory pressure
            for i in range(1000):
                comment = {
                    "id": i,
                    "user": "coderabbitai[bot]",
                    "body": "Large content " * 10000,  # ~130KB per comment
                    "is_coderabbit": True
                }
                large_dataset.append(comment)
                
                # Check memory usage periodically
                if i % 100 == 0:
                    current_memory = self.process.memory_info().rss
                    memory_increase = current_memory - self.initial_memory
                    
                    # Stop if memory usage becomes excessive
                    if memory_increase > 500 * 1024 * 1024:  # > 500MB
                        break
            
            analyzer = CommentAnalyzer()
            result = analyzer.analyze_comments(large_dataset)
            
            # Should handle large dataset gracefully
            self.assertIsInstance(result, dict)
            
        except MemoryError:
            # This is expected behavior under memory pressure
            pass


class TestPerformanceRegression(PerformanceTestBase):
    """Test for performance regressions."""
    
    def test_baseline_performance_metrics(self):
        """Establish baseline performance metrics."""
        # Standard test dataset
        comments = self.generate_large_comment_dataset(100)
        analyzer = CommentAnalyzer()
        
        # Measure multiple runs for consistency
        execution_times = []
        for _ in range(5):
            _, execution_time = self.measure_execution_time(
                analyzer.analyze_comments, comments
            )
            execution_times.append(execution_time)
        
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Performance should be consistent
        self.assertLess(max_time - min_time, avg_time * 0.5)  # Low variation
        self.assertLess(avg_time, 3.0)  # Reasonable baseline
        
        # Log baseline metrics for future comparison
        print(f"Baseline performance metrics:")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Min time: {min_time:.3f}s")
        print(f"  Max time: {max_time:.3f}s")
        print(f"  Variation: {max_time - min_time:.3f}s")


if __name__ == '__main__':
    # Run performance tests with verbose output
    unittest.main(verbosity=2)

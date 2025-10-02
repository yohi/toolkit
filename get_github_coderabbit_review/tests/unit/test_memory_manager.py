"""Tests for MemoryManager and streaming processing utilities."""

import unittest
from unittest.mock import Mock, patch

from coderabbit_fetcher.utils.memory_manager import (
    MemoryManager,
    MemoryStats,
    StreamingProcessor,
    memory_efficient_processing,
)


class TestMemoryStats(unittest.TestCase):
    """Test cases for MemoryStats dataclass."""

    def test_memory_stats_creation(self):
        """Test MemoryStats creation with valid values."""
        stats = MemoryStats(used_mb=100.5, available_mb=200.3, percent_used=50.2, process_mb=75.1)

        self.assertEqual(stats.used_mb, 100.5)
        self.assertEqual(stats.available_mb, 200.3)
        self.assertEqual(stats.percent_used, 50.2)
        self.assertEqual(stats.process_mb, 75.1)


class TestMemoryManager(unittest.TestCase):
    """Test cases for MemoryManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.memory_manager = MemoryManager(max_memory_mb=100)

    @patch("coderabbit_fetcher.utils.memory_manager.psutil")
    def test_get_memory_stats_success(self, mock_psutil):
        """Test successful memory stats retrieval."""
        # Mock psutil objects
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 50 * 1024 * 1024  # 50MB in bytes
        mock_process.memory_info.return_value = mock_memory_info

        mock_virtual_memory = Mock()
        mock_virtual_memory.used = 1000 * 1024 * 1024  # 1000MB
        mock_virtual_memory.available = 500 * 1024 * 1024  # 500MB
        mock_virtual_memory.percent = 66.7

        mock_psutil.Process.return_value = mock_process
        mock_psutil.virtual_memory.return_value = mock_virtual_memory

        stats = self.memory_manager.get_memory_stats()

        self.assertAlmostEqual(stats.used_mb, 1000.0, places=1)
        self.assertAlmostEqual(stats.available_mb, 500.0, places=1)
        self.assertEqual(stats.percent_used, 66.7)
        self.assertAlmostEqual(stats.process_mb, 50.0, places=1)

    @patch("coderabbit_fetcher.utils.memory_manager.psutil")
    def test_get_memory_stats_error(self, mock_psutil):
        """Test memory stats retrieval with error."""
        mock_psutil.Process.side_effect = Exception("psutil error")

        stats = self.memory_manager.get_memory_stats()

        # Should return zero stats on error
        self.assertEqual(stats.used_mb, 0)
        self.assertEqual(stats.available_mb, 0)
        self.assertEqual(stats.percent_used, 0)
        self.assertEqual(stats.process_mb, 0)

    def test_check_memory_pressure_low(self):
        """Test memory pressure check - low pressure."""
        with patch.object(self.memory_manager, "get_memory_stats") as mock_stats:
            mock_stats.return_value = MemoryStats(0, 0, 0, 30)  # 30MB usage

            pressure = self.memory_manager.check_memory_pressure()

            self.assertEqual(pressure, "low")

    def test_check_memory_pressure_medium(self):
        """Test memory pressure check - medium pressure."""
        with patch.object(self.memory_manager, "get_memory_stats") as mock_stats:
            mock_stats.return_value = MemoryStats(0, 0, 0, 65)  # 65MB usage

            pressure = self.memory_manager.check_memory_pressure()

            self.assertEqual(pressure, "medium")

    def test_check_memory_pressure_high(self):
        """Test memory pressure check - high pressure."""
        with patch.object(self.memory_manager, "get_memory_stats") as mock_stats:
            mock_stats.return_value = MemoryStats(0, 0, 0, 85)  # 85MB usage

            pressure = self.memory_manager.check_memory_pressure()

            self.assertEqual(pressure, "high")

    def test_check_memory_pressure_critical(self):
        """Test memory pressure check - critical pressure."""
        with patch.object(self.memory_manager, "get_memory_stats") as mock_stats:
            mock_stats.return_value = MemoryStats(0, 0, 0, 98)  # 98MB usage

            pressure = self.memory_manager.check_memory_pressure()

            self.assertEqual(pressure, "critical")

    @patch("coderabbit_fetcher.utils.memory_manager.gc")
    def test_optimize_memory_force(self, mock_gc):
        """Test forced memory optimization."""
        mock_gc.collect.return_value = 10

        result = self.memory_manager.optimize_memory(force=True)

        self.assertTrue(result)
        mock_gc.collect.assert_called_once()

    @patch("coderabbit_fetcher.utils.memory_manager.gc")
    def test_optimize_memory_high_pressure(self, mock_gc):
        """Test memory optimization with high pressure."""
        mock_gc.collect.return_value = 5

        with patch.object(self.memory_manager, "check_memory_pressure") as mock_pressure:
            mock_pressure.return_value = "high"

            result = self.memory_manager.optimize_memory()

            self.assertTrue(result)
            mock_gc.collect.assert_called_once()

    def test_optimize_memory_low_pressure(self):
        """Test memory optimization with low pressure."""
        with patch.object(self.memory_manager, "check_memory_pressure") as mock_pressure:
            mock_pressure.return_value = "low"

            result = self.memory_manager.optimize_memory()

            self.assertFalse(result)

    def test_stream_large_list_basic(self):
        """Test streaming large list in batches."""
        large_list = list(range(100))
        batches = list(self.memory_manager.stream_large_list(large_list, batch_size=10))

        self.assertEqual(len(batches), 10)
        self.assertEqual(len(batches[0]), 10)
        self.assertEqual(batches[0], list(range(10)))
        self.assertEqual(batches[-1], list(range(90, 100)))

    def test_stream_large_list_with_memory_optimization(self):
        """Test streaming with memory optimization."""
        large_list = list(range(200))

        with patch.object(self.memory_manager, "check_memory_pressure") as mock_pressure:
            with patch.object(self.memory_manager, "optimize_memory") as mock_optimize:
                # Simulate critical pressure on first batch
                mock_pressure.side_effect = ["critical", "low", "low", "low"]

                batches = list(self.memory_manager.stream_large_list(large_list, batch_size=50))

                self.assertEqual(len(batches), 4)
                mock_optimize.assert_called()

    def test_process_with_memory_limit_basic(self):
        """Test processing with memory limit protection."""
        items = [1, 2, 3, 4, 5]

        def double_processor(item):
            return item * 2

        results = self.memory_manager.process_with_memory_limit(items, double_processor)

        self.assertEqual(results, [2, 4, 6, 8, 10])

    def test_process_with_memory_limit_low_memory(self):
        """Test processing with low available memory."""
        items = list(range(100))

        def identity_processor(item):
            return item

        with patch.object(self.memory_manager, "get_memory_stats") as mock_stats:
            mock_stats.return_value = MemoryStats(0, 150, 0, 0)  # Low available memory

            results = self.memory_manager.process_with_memory_limit(
                items, identity_processor, batch_size=50
            )

            self.assertEqual(len(results), 100)
            self.assertEqual(results, items)

    def test_process_with_memory_limit_processor_error(self):
        """Test processing with processor function errors."""
        items = [1, 2, 3, "invalid", 5]

        def strict_doubler(item):
            if not isinstance(item, int):
                raise ValueError("Invalid item")
            return item * 2

        # Should handle errors gracefully and continue processing
        results = self.memory_manager.process_with_memory_limit(items, strict_doubler)

        # Should process valid items and skip invalid ones
        self.assertEqual(len(results), 4)  # 4 valid integers
        self.assertIn(2, results)
        self.assertIn(10, results)


class TestStreamingProcessor(unittest.TestCase):
    """Test cases for StreamingProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.stream_processor = StreamingProcessor()

    def test_stream_comments_basic(self):
        """Test basic comment streaming."""
        comments = [{"id": i, "body": f"Comment {i}"} for i in range(5)]

        batches = list(self.stream_processor.stream_comments(comments, batch_size=2))

        self.assertEqual(len(batches), 3)  # 5 comments in batches of 2
        self.assertEqual(len(batches[0]), 2)
        self.assertEqual(len(batches[1]), 2)
        self.assertEqual(len(batches[2]), 1)

    def test_process_comments_streaming_basic(self):
        """Test streaming comment processing."""
        comments = [{"id": i, "body": f"Comment {i}"} for i in range(10)]

        def extract_id(comment):
            return comment["id"]

        results = self.stream_processor.process_comments_streaming(comments, extract_id)

        self.assertEqual(len(results), 10)
        self.assertEqual(results, list(range(10)))

    def test_process_comments_streaming_with_errors(self):
        """Test streaming processing with processor errors."""
        comments = [{"id": i} for i in range(5)]

        def failing_processor(comment):
            if comment["id"] == 2:
                raise ValueError("Test error")
            return comment["id"]

        results = self.stream_processor.process_comments_streaming(comments, failing_processor)

        # Should continue processing despite errors
        self.assertEqual(len(results), 4)  # 5 - 1 error
        self.assertNotIn(2, results)

    def test_chunk_large_content_small(self):
        """Test chunking small content."""
        content = "Small content"

        chunks = self.stream_processor.chunk_large_content(content, max_chunk_size=100)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], content)

    def test_chunk_large_content_large(self):
        """Test chunking large content."""
        content = "x" * 25000  # 25KB content

        chunks = self.stream_processor.chunk_large_content(content, max_chunk_size=10000)

        self.assertEqual(len(chunks), 3)  # 25000 / 10000 = 2.5, rounded up to 3
        self.assertTrue(all(len(chunk) <= 10000 for chunk in chunks))


class TestMemoryEfficientProcessingDecorator(unittest.TestCase):
    """Test cases for memory_efficient_processing decorator."""

    def test_memory_efficient_processing_decorator(self):
        """Test memory efficient processing decorator."""

        @memory_efficient_processing
        def test_function(x):
            return x * 2

        result = test_function(5)

        self.assertEqual(result, 10)

    def test_memory_efficient_processing_with_exception(self):
        """Test decorator behavior with exceptions."""

        @memory_efficient_processing
        def failing_function():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            failing_function()

    @patch("coderabbit_fetcher.utils.memory_manager.MemoryManager")
    def test_memory_efficient_processing_optimization(self, mock_memory_manager_class):
        """Test that decorator performs memory optimization."""
        mock_manager = Mock()
        mock_memory_manager_class.return_value = mock_manager

        @memory_efficient_processing
        def test_function():
            return "success"

        result = test_function()

        self.assertEqual(result, "success")
        mock_manager.optimize_memory.assert_called_with(force=True)


if __name__ == "__main__":
    unittest.main()

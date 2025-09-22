"""Memory management utilities for large dataset processing."""

import gc
import logging
import psutil
from typing import Iterator, List, Any, Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    used_mb: float
    available_mb: float
    percent_used: float
    process_mb: float


class MemoryManager:
    """Manages memory usage during large dataset processing."""

    def __init__(self, max_memory_mb: int = 500):
        """Initialize memory manager.

        Args:
            max_memory_mb: Maximum memory usage threshold in MB
        """
        self.max_memory_mb = max_memory_mb
        self.warning_threshold = max_memory_mb * 0.8
        self.critical_threshold = max_memory_mb * 0.95

    def get_memory_stats(self) -> MemoryStats:
        """Get current memory usage statistics.

        Returns:
            MemoryStats object with current usage
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()

            return MemoryStats(
                used_mb=system_memory.used / 1024 / 1024,
                available_mb=system_memory.available / 1024 / 1024,
                percent_used=system_memory.percent,
                process_mb=memory_info.rss / 1024 / 1024
            )
        except Exception as e:
            logger.warning(f"Failed to get memory stats: {e}")
            return MemoryStats(0, 0, 0, 0)

    def check_memory_pressure(self) -> str:
        """Check current memory pressure level.

        Returns:
            Pressure level: 'low', 'medium', 'high', 'critical'
        """
        stats = self.get_memory_stats()

        if stats.process_mb >= self.critical_threshold:
            return 'critical'
        elif stats.process_mb >= self.warning_threshold:
            return 'high'
        elif stats.process_mb >= self.max_memory_mb * 0.6:
            return 'medium'
        else:
            return 'low'

    def optimize_memory(self, force: bool = False) -> bool:
        """Optimize memory usage by forcing garbage collection.

        Args:
            force: Force optimization regardless of pressure level

        Returns:
            True if optimization was performed
        """
        pressure = self.check_memory_pressure()

        if force or pressure in ['high', 'critical']:
            logger.debug(f"Optimizing memory (pressure: {pressure})")

            # Force garbage collection
            collected = gc.collect()

            logger.debug(f"Garbage collection freed {collected} objects")
            return True

        return False

    def stream_large_list(self, large_list: List[Any], batch_size: int = 100) -> Iterator[List[Any]]:
        """Stream large list in batches to reduce memory usage.

        Args:
            large_list: Large list to process
            batch_size: Size of each batch

        Yields:
            Batches of items from the large list
        """
        total_items = len(large_list)
        logger.debug(f"Streaming {total_items} items in batches of {batch_size}")

        for i in range(0, total_items, batch_size):
            batch = large_list[i:i + batch_size]

            # Check memory pressure before yielding batch
            pressure = self.check_memory_pressure()
            if pressure == 'critical':
                logger.warning("Critical memory pressure detected, forcing optimization")
                self.optimize_memory(force=True)

            yield batch

            # Optimize memory after processing larger batches
            if len(batch) >= 50:
                self.optimize_memory()

    def process_with_memory_limit(self, items: List[Any], processor_func, **kwargs) -> List[Any]:
        """Process items with memory limit protection.

        Args:
            items: Items to process
            processor_func: Function to process each item
            **kwargs: Additional arguments for processor function

        Returns:
            List of processed results
        """
        results = []
        batch_size = kwargs.get('batch_size', 100)

        # Adjust batch size based on available memory
        stats = self.get_memory_stats()
        if stats.available_mb < 200:  # Less than 200MB available
            batch_size = min(batch_size, 25)
        elif stats.available_mb < 500:  # Less than 500MB available
            batch_size = min(batch_size, 50)

        logger.debug(f"Processing {len(items)} items with batch size {batch_size}")

        for batch in self.stream_large_list(items, batch_size):
            try:
                # Process batch
                batch_results = []
                for item in batch:
                    result = processor_func(item, **kwargs)
                    if result is not None:
                        batch_results.append(result)

                results.extend(batch_results)

                # Log progress for large datasets
                if len(items) > 500:
                    progress = len(results) / len(items) * 100
                    logger.debug(f"Progress: {progress:.1f}% ({len(results)}/{len(items)})")

            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                continue

        return results


class StreamingProcessor:
    """Streaming processor for large comment datasets."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """Initialize streaming processor.

        Args:
            memory_manager: Memory manager instance
        """
        self.memory_manager = memory_manager or MemoryManager()

    def stream_comments(self, comments: List[Dict[str, Any]], batch_size: int = 50) -> Iterator[List[Dict[str, Any]]]:
        """Stream comments in memory-efficient batches.

        Args:
            comments: List of comment dictionaries
            batch_size: Size of each batch

        Yields:
            Batches of comments
        """
        return self.memory_manager.stream_large_list(comments, batch_size)

    def process_comments_streaming(self, comments: List[Dict[str, Any]], processor_func) -> List[Any]:
        """Process comments using streaming approach.

        Args:
            comments: List of comment dictionaries
            processor_func: Function to process each comment

        Returns:
            List of processed results
        """
        logger.info(f"Starting streaming processing of {len(comments)} comments")

        results = []
        processed_count = 0

        for batch in self.stream_comments(comments):
            try:
                # Process batch
                for comment in batch:
                    result = processor_func(comment)
                    if result is not None:
                        results.append(result)
                    processed_count += 1

                # Log progress periodically
                if processed_count % 100 == 0:
                    memory_stats = self.memory_manager.get_memory_stats()
                    logger.debug(
                        f"Processed {processed_count}/{len(comments)} comments, "
                        f"memory usage: {memory_stats.process_mb:.1f}MB"
                    )

                # Optimize memory if needed
                self.memory_manager.optimize_memory()

            except Exception as e:
                logger.error(f"Error processing comment batch: {e}")
                continue

        logger.info(f"Streaming processing completed: {len(results)} results from {processed_count} comments")
        return results

    def chunk_large_content(self, content: str, max_chunk_size: int = 10000) -> List[str]:
        """Chunk large content strings to reduce memory pressure.

        Args:
            content: Large content string
            max_chunk_size: Maximum size of each chunk

        Returns:
            List of content chunks
        """
        if len(content) <= max_chunk_size:
            return [content]

        chunks = []
        for i in range(0, len(content), max_chunk_size):
            chunk = content[i:i + max_chunk_size]
            chunks.append(chunk)

        logger.debug(f"Chunked content into {len(chunks)} pieces")
        return chunks


def memory_efficient_processing(func):
    """Decorator for memory-efficient processing of functions.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with memory optimization
    """
    def wrapper(*args, **kwargs):
        memory_manager = MemoryManager()

        # Log initial memory state
        initial_stats = memory_manager.get_memory_stats()
        logger.debug(f"Starting {func.__name__}, memory usage: {initial_stats.process_mb:.1f}MB")

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Optimize memory after execution
            memory_manager.optimize_memory(force=True)

            # Log final memory state
            final_stats = memory_manager.get_memory_stats()
            memory_diff = final_stats.process_mb - initial_stats.process_mb
            logger.debug(
                f"Completed {func.__name__}, memory usage: {final_stats.process_mb:.1f}MB "
                f"(diff: {memory_diff:+.1f}MB)"
            )

            return result

        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            # Try to recover memory even on error
            memory_manager.optimize_memory(force=True)
            raise

    return wrapper

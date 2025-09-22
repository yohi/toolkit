"""Streaming processing utilities for large datasets."""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, Iterator, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for streaming processing."""

    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    start_time: float
    current_time: float

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        return (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        return self.current_time - self.start_time

    @property
    def items_per_second(self) -> float:
        """Calculate processing rate."""
        return self.processed_items / self.elapsed_time if self.elapsed_time > 0 else 0


class StreamingProcessor:
    """Advanced streaming processor with parallel processing capabilities."""

    def __init__(self, max_workers: int = 3, batch_size: int = 50):
        """Initialize streaming processor.

        Args:
            max_workers: Maximum number of worker threads
            batch_size: Default batch size for processing
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.stats_lock = threading.Lock()

    def stream_with_batching(
        self, items: List[Any], batch_size: Optional[int] = None
    ) -> Iterator[List[Any]]:
        """Stream items in batches.

        Args:
            items: List of items to stream
            batch_size: Size of each batch (defaults to instance batch_size)

        Yields:
            Batches of items
        """
        effective_batch_size = batch_size or self.batch_size
        total_items = len(items)

        logger.debug(f"Streaming {total_items} items in batches of {effective_batch_size}")

        for i in range(0, total_items, effective_batch_size):
            batch = items[i : i + effective_batch_size]
            yield batch

    def process_streaming(
        self,
        items: List[Any],
        processor_func: Callable[[Any], Any],
        batch_size: Optional[int] = None,
        parallel: bool = True,
        progress_callback: Optional[Callable[[ProcessingStats], None]] = None,
    ) -> List[Any]:
        """Process items using streaming approach with optional parallelization.

        Args:
            items: Items to process
            processor_func: Function to process each item
            batch_size: Size of each batch
            parallel: Whether to use parallel processing
            progress_callback: Optional callback for progress updates

        Returns:
            List of processed results
        """
        total_items = len(items)
        start_time = time.time()

        logger.info(f"Starting streaming processing of {total_items} items (parallel={parallel})")

        results = []
        processed_count = 0
        success_count = 0
        failed_count = 0

        effective_batch_size = batch_size or self.batch_size

        for batch in self.stream_with_batching(items, effective_batch_size):
            if parallel and len(batch) > 1:
                # Use parallel processing for larger batches
                batch_results = self._process_batch_parallel(batch, processor_func)
            else:
                # Use sequential processing for smaller batches
                batch_results = self._process_batch_sequential(batch, processor_func)

            # Collect results and update statistics
            for result in batch_results:
                if result is not None:
                    results.append(result)
                    success_count += 1
                else:
                    failed_count += 1
                processed_count += 1

            # Update progress
            if progress_callback:
                stats = ProcessingStats(
                    total_items=total_items,
                    processed_items=processed_count,
                    successful_items=success_count,
                    failed_items=failed_count,
                    start_time=start_time,
                    current_time=time.time(),
                )
                progress_callback(stats)

            # Log progress for large datasets
            if total_items > 100 and processed_count % 50 == 0:
                progress = processed_count / total_items * 100
                elapsed = time.time() - start_time
                rate = processed_count / elapsed if elapsed > 0 else 0
                logger.debug(
                    f"Progress: {progress:.1f}% ({processed_count}/{total_items}), "
                    f"rate: {rate:.1f} items/sec"
                )

        elapsed_time = time.time() - start_time
        logger.info(
            f"Streaming processing completed: {success_count} successful, "
            f"{failed_count} failed, {elapsed_time:.2f}s total"
        )

        return results

    def _process_batch_sequential(
        self, batch: List[Any], processor_func: Callable[[Any], Any]
    ) -> List[Any]:
        """Process batch sequentially.

        Args:
            batch: Batch of items to process
            processor_func: Processing function

        Returns:
            List of processed results
        """
        results = []

        for item in batch:
            try:
                result = processor_func(item)
                results.append(result)
            except Exception as e:
                logger.warning(f"Error processing item: {e}")
                results.append(None)

        return results

    def _process_batch_parallel(
        self, batch: List[Any], processor_func: Callable[[Any], Any]
    ) -> List[Any]:
        """Process batch in parallel using ThreadPoolExecutor.

        Args:
            batch: Batch of items to process
            processor_func: Processing function

        Returns:
            List of processed results
        """
        results = [None] * len(batch)

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(batch))) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(processor_func, item): idx for idx, item in enumerate(batch)
            }

            # Collect results maintaining order
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    result = future.result()
                    results[idx] = result
                except Exception as e:
                    logger.warning(f"Error processing item {idx}: {e}")
                    results[idx] = None

        return results

    def stream_and_filter(
        self, items: List[Any], filter_func: Callable[[Any], bool], batch_size: Optional[int] = None
    ) -> Generator[Any, None, None]:
        """Stream items and apply filtering.

        Args:
            items: Items to stream and filter
            filter_func: Function to filter items
            batch_size: Size of each batch

        Yields:
            Filtered items
        """
        for batch in self.stream_with_batching(items, batch_size):
            for item in batch:
                try:
                    if filter_func(item):
                        yield item
                except Exception as e:
                    logger.warning(f"Error filtering item: {e}")
                    continue

    def stream_and_transform(
        self,
        items: List[Any],
        transform_func: Callable[[Any], Any],
        batch_size: Optional[int] = None,
        parallel: bool = True,
    ) -> Generator[Any, None, None]:
        """Stream items and apply transformation.

        Args:
            items: Items to stream and transform
            transform_func: Function to transform items
            batch_size: Size of each batch
            parallel: Whether to use parallel processing

        Yields:
            Transformed items
        """
        for batch in self.stream_with_batching(items, batch_size):
            if parallel and len(batch) > 1:
                batch_results = self._process_batch_parallel(batch, transform_func)
            else:
                batch_results = self._process_batch_sequential(batch, transform_func)

            for result in batch_results:
                if result is not None:
                    yield result

    def adaptive_batch_size(self, items: List[Any], target_time_per_batch: float = 1.0) -> int:
        """Calculate adaptive batch size based on target processing time.

        Args:
            items: Items to process
            target_time_per_batch: Target time per batch in seconds

        Returns:
            Recommended batch size
        """
        if len(items) < 10:
            return len(items)

        # Start with a small sample to measure processing time
        sample_size = min(5, len(items))
        start_time = time.time()

        # Process sample to estimate time per item
        try:
            for i in range(sample_size):
                # Simulate minimal processing
                str(items[i])
        except Exception:
            pass

        elapsed = time.time() - start_time
        time_per_item = elapsed / sample_size if sample_size > 0 else 0.01

        # Calculate batch size to reach target time
        if time_per_item > 0:
            recommended_batch_size = max(1, int(target_time_per_batch / time_per_item))
        else:
            recommended_batch_size = self.batch_size

        # Clamp to reasonable bounds
        recommended_batch_size = min(max(recommended_batch_size, 10), 200)

        logger.debug(
            f"Adaptive batch size: {recommended_batch_size} (target: {target_time_per_batch}s)"
        )
        return recommended_batch_size


class CommentStreamProcessor(StreamingProcessor):
    """Specialized streaming processor for CodeRabbit comments."""

    def __init__(self, max_workers: int = 3, batch_size: int = 25):
        """Initialize comment stream processor.

        Args:
            max_workers: Maximum number of worker threads
            batch_size: Default batch size for comment processing
        """
        super().__init__(max_workers, batch_size)

    def stream_coderabbit_comments(
        self, comments: List[Dict[str, Any]], filter_coderabbit: bool = True
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream CodeRabbit comments with filtering.

        Args:
            comments: List of comment dictionaries
            filter_coderabbit: Whether to filter for CodeRabbit comments only

        Yields:
            CodeRabbit comment dictionaries
        """

        def is_coderabbit_comment(comment: Dict[str, Any]) -> bool:
            """Check if comment is from CodeRabbit."""
            if not filter_coderabbit:
                return True

            user = comment.get("user", {})
            login = user.get("login", "").lower()
            return "coderabbit" in login

        yield from self.stream_and_filter(comments, is_coderabbit_comment)

    def process_comments_by_type(
        self, comments: List[Dict[str, Any]], processors: Dict[str, Callable[[Dict[str, Any]], Any]]
    ) -> Dict[str, List[Any]]:
        """Process comments by type using different processors.

        Args:
            comments: List of comment dictionaries
            processors: Dictionary mapping comment types to processing functions

        Returns:
            Dictionary mapping comment types to processed results
        """
        results = {comment_type: [] for comment_type in processors.keys()}

        def categorize_comment(comment: Dict[str, Any]) -> str:
            """Categorize comment by type."""
            body = comment.get("body", "").lower()

            if "actionable comments" in body:
                return "actionable"
            elif "nitpick" in body:
                return "nitpick"
            elif "outside diff" in body:
                return "outside_diff"
            elif "🤖" in body or "ai agent" in body:
                return "ai_agent"
            else:
                return "general"

        # Group comments by type
        comments_by_type = {}
        for comment in comments:
            comment_type = categorize_comment(comment)
            if comment_type not in comments_by_type:
                comments_by_type[comment_type] = []
            comments_by_type[comment_type].append(comment)

        # Process each type using appropriate processor
        for comment_type, type_comments in comments_by_type.items():
            if comment_type in processors:
                processor_func = processors[comment_type]
                type_results = self.process_streaming(
                    type_comments, processor_func, parallel=len(type_comments) > 5
                )
                results[comment_type].extend(type_results)
            else:
                logger.debug(f"No processor for comment type: {comment_type}")

        return results

    def optimize_for_large_pr(self, comment_count: int) -> Dict[str, Any]:
        """Optimize processing settings for large PRs.

        Args:
            comment_count: Number of comments to process

        Returns:
            Dictionary with optimized settings
        """
        if comment_count <= 50:
            return {"batch_size": 10, "max_workers": 2, "parallel_threshold": 5}
        elif comment_count <= 200:
            return {"batch_size": 25, "max_workers": 3, "parallel_threshold": 10}
        else:
            return {"batch_size": 50, "max_workers": 4, "parallel_threshold": 20}

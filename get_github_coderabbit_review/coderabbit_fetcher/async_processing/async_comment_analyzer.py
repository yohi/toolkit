"""Async comment analyzer for CodeRabbit fetcher."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from ..comment_analyzer import CommentAnalyzer
from ..models import AnalyzedComments
from ..patterns.observer import EventType, publish_event

logger = logging.getLogger(__name__)


class AsyncCommentAnalyzer:
    """Async comment analyzer with parallel processing capabilities."""

    def __init__(self, max_workers: int = 4):
        """Initialize async comment analyzer.

        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.sync_analyzer = CommentAnalyzer()

    async def analyze_comments_async(
        self, comments: List[Dict[str, Any]], batch_size: int = 20, session_id: Optional[str] = None
    ) -> AnalyzedComments:
        """Analyze comments asynchronously with batching.

        Args:
            comments: List of comment dictionaries
            batch_size: Size of processing batches
            session_id: Optional session identifier for event tracking

        Returns:
            Analyzed comments result
        """
        start_time = time.time()
        total_comments = len(comments)

        logger.info(f"Starting async analysis of {total_comments} comments")

        # Publish start event
        if session_id:
            publish_event(
                EventType.PROGRESS_UPDATE,
                source="AsyncCommentAnalyzer",
                data={
                    "phase": "comment_analysis_started",
                    "total_comments": total_comments,
                    "batch_size": batch_size,
                },
                session_id=session_id,
            )

        try:
            if not comments:
                return AnalyzedComments(
                    summary_comments=[],
                    review_comments=[],
                    unresolved_threads=[],
                    metadata={"total_comments": 0, "processing_time": 0},
                )

            # Filter CodeRabbit comments first
            coderabbit_comments = await self._filter_coderabbit_comments_async(comments)

            if not coderabbit_comments:
                logger.warning("No CodeRabbit comments found")
                return AnalyzedComments(
                    summary_comments=[],
                    review_comments=[],
                    unresolved_threads=[],
                    metadata={
                        "total_comments": total_comments,
                        "coderabbit_comments": 0,
                        "processing_time": time.time() - start_time,
                    },
                )

            # Process comments in parallel batches
            analyzed_results = await self._process_comments_in_batches(
                coderabbit_comments, batch_size, session_id
            )

            # Combine results
            final_result = await self._combine_analysis_results(analyzed_results, session_id)

            processing_time = time.time() - start_time

            # Update metadata
            final_result.metadata.update(
                {
                    "total_comments": total_comments,
                    "coderabbit_comments": len(coderabbit_comments),
                    "processing_time": processing_time,
                    "async_processing": True,
                    "batch_count": len(analyzed_results),
                }
            )

            # Publish completion event
            if session_id:
                publish_event(
                    EventType.PROGRESS_UPDATE,
                    source="AsyncCommentAnalyzer",
                    data={
                        "phase": "comment_analysis_completed",
                        "processing_time": processing_time,
                        "total_analyzed": len(coderabbit_comments),
                    },
                    session_id=session_id,
                )

            logger.info(f"Async comment analysis completed in {processing_time:.2f}s")
            return final_result

        except Exception as e:
            # Publish error event
            if session_id:
                publish_event(
                    EventType.PROCESSING_FAILED,
                    source="AsyncCommentAnalyzer",
                    data={"phase": "comment_analysis_failed", "error": str(e)},
                    severity="error",
                    session_id=session_id,
                )

            logger.error(f"Error in async comment analysis: {e}")
            raise

    async def _filter_coderabbit_comments_async(
        self, comments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter CodeRabbit comments asynchronously.

        Args:
            comments: List of all comments

        Returns:
            List of CodeRabbit comments
        """

        def filter_coderabbit(comment_batch):
            """Filter function to run in thread pool."""
            filtered = []
            for comment in comment_batch:
                user = comment.get("user", {})
                login = user.get("login", "").lower()
                if "coderabbit" in login:
                    filtered.append(comment)
            return filtered

        # Process in chunks to avoid blocking
        chunk_size = 100
        chunks = [comments[i : i + chunk_size] for i in range(0, len(comments), chunk_size)]

        # Run filtering in thread pool
        loop = asyncio.get_running_loop()
        tasks = [loop.run_in_executor(self.executor, filter_coderabbit, chunk) for chunk in chunks]

        results = await asyncio.gather(*tasks)

        # Flatten results
        coderabbit_comments = []
        for chunk_results in results:
            coderabbit_comments.extend(chunk_results)

        logger.info(
            f"Filtered {len(coderabbit_comments)} CodeRabbit comments from {len(comments)} total"
        )
        return coderabbit_comments

    async def _process_comments_in_batches(
        self, comments: List[Dict[str, Any]], batch_size: int, session_id: Optional[str] = None
    ) -> List[AnalyzedComments]:
        """Process comments in parallel batches.

        Args:
            comments: List of comments to process
            batch_size: Size of each batch
            session_id: Optional session identifier

        Returns:
            List of analysis results from each batch
        """
        # Create batches
        batches = [comments[i : i + batch_size] for i in range(0, len(comments), batch_size)]
        total_batches = len(batches)

        logger.info(f"Processing {len(comments)} comments in {total_batches} batches")

        # Process batches with controlled concurrency
        semaphore = asyncio.Semaphore(self.max_workers)

        async def run_batch(i: int, batch):
            async with semaphore:
                return await self._process_single_batch(batch, i + 1, total_batches, session_id)

        # Execute all batch tasks (bounded)
        try:
            results = await asyncio.gather(
                *[
                    asyncio.create_task(run_batch(i, batch), name=f"batch_{i + 1}")
                    for i, batch in enumerate(batches)
                ],
                return_exceptions=True,
            )

            # Filter out exceptions and log errors
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch {i + 1} failed: {result}")
                else:
                    valid_results.append(result)

            logger.info(
                f"Successfully processed {len(valid_results)} out of {total_batches} batches"
            )
            return valid_results

        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            raise

    async def _process_single_batch(
        self,
        batch: List[Dict[str, Any]],
        batch_number: int,
        total_batches: int,
        session_id: Optional[str] = None,
    ) -> AnalyzedComments:
        """Process a single batch of comments.

        Args:
            batch: Batch of comments to process
            batch_number: Current batch number
            total_batches: Total number of batches
            session_id: Optional session identifier

        Returns:
            Analysis results for the batch
        """
        logger.debug(f"Processing batch {batch_number}/{total_batches} ({len(batch)} comments)")

        # Publish progress update
        if session_id:
            publish_event(
                EventType.PROGRESS_UPDATE,
                source="AsyncCommentAnalyzer",
                data={
                    "phase": "batch_processing",
                    "batch_number": batch_number,
                    "total_batches": total_batches,
                    "batch_size": len(batch),
                },
                session_id=session_id,
            )

        try:
            # Run synchronous analysis in thread pool
            loop = asyncio.get_running_loop()

            # Create a synthetic PR data structure for the batch
            pr_data = {
                "comments": batch,
                "reviews": [],  # Reviews are typically in the comments already
                "files": [],
            }

            # Execute sync analysis in thread pool
            result = await loop.run_in_executor(
                self.executor, self.sync_analyzer.analyze_comments, pr_data
            )

            logger.debug(f"Batch {batch_number} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error processing batch {batch_number}: {e}")
            # Return empty result for failed batch
            return AnalyzedComments(
                summary_comments=[],
                review_comments=[],
                unresolved_threads=[],
                metadata={"batch_error": str(e), "batch_number": batch_number},
            )

    async def _combine_analysis_results(
        self, results: List[AnalyzedComments], session_id: Optional[str] = None
    ) -> AnalyzedComments:
        """Combine multiple analysis results into a single result.

        Args:
            results: List of analysis results to combine
            session_id: Optional session identifier

        Returns:
            Combined analysis result
        """
        if not results:
            return AnalyzedComments(
                summary_comments=[],
                review_comments=[],
                unresolved_threads=[],
                metadata={"error": "No valid results to combine"},
            )

        logger.info(f"Combining {len(results)} analysis results")

        # Publish progress
        if session_id:
            publish_event(
                EventType.PROGRESS_UPDATE,
                source="AsyncCommentAnalyzer",
                data={"phase": "combining_results", "result_count": len(results)},
                session_id=session_id,
            )

        # Run combination in thread pool to avoid blocking
        loop = asyncio.get_running_loop()

        def combine_sync():
            """Synchronous combination logic."""
            combined_summary_comments = []
            combined_review_comments = []
            combined_unresolved_threads = []
            combined_metadata = {}

            # Combine all components
            for result in results:
                combined_summary_comments.extend(result.summary_comments)
                combined_review_comments.extend(result.review_comments)
                combined_unresolved_threads.extend(result.unresolved_threads)

                # Merge metadata
                for key, value in result.metadata.items():
                    if key in combined_metadata:
                        # Handle numeric values by summing
                        if isinstance(value, (int, float)) and isinstance(
                            combined_metadata[key], (int, float)
                        ):
                            combined_metadata[key] += value
                        # Handle lists by extending
                        elif isinstance(value, list) and isinstance(combined_metadata[key], list):
                            combined_metadata[key].extend(value)
                        # Handle other cases by keeping first value
                    else:
                        combined_metadata[key] = value

            # Add combination metadata
            combined_metadata["combined_from_batches"] = len(results)
            combined_metadata["total_summary_comments"] = len(combined_summary_comments)
            combined_metadata["total_review_comments"] = len(combined_review_comments)
            combined_metadata["total_unresolved_threads"] = len(combined_unresolved_threads)

            return AnalyzedComments(
                summary_comments=combined_summary_comments,
                review_comments=combined_review_comments,
                unresolved_threads=combined_unresolved_threads,
                metadata=combined_metadata,
            )

        # Execute combination in thread pool
        combined_result = await loop.run_in_executor(self.executor, combine_sync)

        logger.info(
            f"Combined results: {len(combined_result.summary_comments)} summary, "
            f"{len(combined_result.review_comments)} review, "
            f"{len(combined_result.unresolved_threads)} unresolved threads"
        )

        return combined_result

    async def close(self) -> None:
        """Close the async comment analyzer and cleanup resources."""
        if self.executor:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.executor.shutdown, True)
            logger.info("AsyncCommentAnalyzer executor shut down")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

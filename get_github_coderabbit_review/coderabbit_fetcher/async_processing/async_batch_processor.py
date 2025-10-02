"""Async batch processor for CodeRabbit fetcher."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class AsyncBatchProcessor:
    """Async batch processor for various data types."""

    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        """Initialize async batch processor.

        Args:
            max_workers: Maximum number of worker threads
            batch_size: Default batch size for processing
        """
        self.max_workers = max_workers
        self.default_batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_files_async(
        self, files: List[Dict[str, Any]], batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process PR files asynchronously.

        Args:
            files: List of file dictionaries
            batch_size: Batch size for processing

        Returns:
            File analysis results
        """
        if not files:
            return {"total_files": 0, "analysis": {}}

        batch_size = batch_size or self.default_batch_size
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        start_time = time.time()

        logger.info(f"Processing {len(files)} files in batches of {batch_size}")

        try:
            # Create batches
            batches = [files[i : i + batch_size] for i in range(0, len(files), batch_size)]

            # Execute with controlled concurrency
            semaphore = asyncio.Semaphore(self.max_workers)

            async def run_batch(i: int, batch):
                async with semaphore:
                    return await self._process_file_batch(batch, i + 1, len(batches))

            results = await asyncio.gather(
                *[
                    asyncio.create_task(run_batch(i, batch), name=f"file_batch_{i + 1}")
                    for i, batch in enumerate(batches)
                ],
                return_exceptions=True,
            )

            # Combine results
            analysis = await self._combine_file_results(results)

            processing_time = time.time() - start_time

            return {
                "total_files": len(files),
                "processing_time": processing_time,
                "batch_count": len(batches),
                "analysis": analysis,
            }

        except Exception as e:
            logger.error(f"Error processing files: {e}")
            return {"total_files": len(files), "error": str(e)}

    async def process_commits_async(
        self, commits: List[Dict[str, Any]], batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process PR commits asynchronously.

        Args:
            commits: List of commit dictionaries
            batch_size: Batch size for processing

        Returns:
            Commit analysis results
        """
        if not commits:
            return {"total_commits": 0, "analysis": {}}

        batch_size = batch_size or self.default_batch_size
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        start_time = time.time()

        logger.info(f"Processing {len(commits)} commits in batches of {batch_size}")

        try:
            # Create batches
            batches = [commits[i : i + batch_size] for i in range(0, len(commits), batch_size)]

            # Execute with controlled concurrency
            semaphore = asyncio.Semaphore(self.max_workers)

            async def run_batch(i: int, batch):
                async with semaphore:
                    return await self._process_commit_batch(batch, i + 1, len(batches))

            results = await asyncio.gather(
                *[
                    asyncio.create_task(run_batch(i, batch), name=f"commit_batch_{i + 1}")
                    for i, batch in enumerate(batches)
                ],
                return_exceptions=True,
            )

            # Combine results
            analysis = await self._combine_commit_results(results)

            processing_time = time.time() - start_time

            return {
                "total_commits": len(commits),
                "processing_time": processing_time,
                "batch_count": len(batches),
                "analysis": analysis,
            }

        except Exception as e:
            logger.error(f"Error processing commits: {e}")
            return {"total_commits": len(commits), "error": str(e)}

    async def process_generic_batch_async(
        self,
        items: List[Any],
        processor_func: Callable[[Any], Any],
        batch_size: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ) -> List[Any]:
        """Process generic items in batches asynchronously.

        Args:
            items: List of items to process
            processor_func: Function to process each item
            batch_size: Batch size for processing
            max_concurrent: Maximum concurrent batches

        Returns:
            List of processed results
        """
        if not items:
            return []

        batch_size = batch_size or self.default_batch_size
        max_concurrent = max_concurrent or self.max_workers
        
        # Validate parameters
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be > 0")

        logger.info(f"Processing {len(items)} items in batches of {batch_size}")

        try:
            import inspect
            
            # Handle async functions differently
            if inspect.iscoroutinefunction(processor_func):
                # For async functions: process items individually with concurrency control
                sem = asyncio.Semaphore(max_concurrent)
                
                async def run_item(item):
                    async with sem:
                        try:
                            return await processor_func(item)
                        except Exception as e:
                            logger.warning(f"Error processing item: {e}")
                            return None
                
                results_list = await asyncio.gather(
                    *(run_item(it) for it in items),
                    return_exceptions=False
                )
                all_results = [r for r in results_list if r is not None]
                logger.info(f"Processed {len(all_results)} items successfully")
                return all_results
            
            # For sync functions: use batch processing with thread pool
            batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_batch_with_semaphore(batch):
                async with semaphore:
                    return await self._process_generic_batch(batch, processor_func)

            # Execute all batches
            results = await asyncio.gather(
                *[process_batch_with_semaphore(batch) for batch in batches],
                return_exceptions=True
            )

            # Flatten results and filter out exceptions
            all_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                elif isinstance(result, list):
                    all_results.extend(result)

            logger.info(f"Processed {len(all_results)} items successfully")
            return all_results

        except Exception as e:
            logger.error(f"Error in generic batch processing: {e}")
            return []

    async def _process_file_batch(
        self, file_batch: List[Dict[str, Any]], batch_number: int, total_batches: int
    ) -> Dict[str, Any]:
        """Process a batch of files.

        Args:
            file_batch: Batch of files to process
            batch_number: Current batch number
            total_batches: Total number of batches

        Returns:
            Batch processing results
        """
        logger.debug(f"Processing file batch {batch_number}/{total_batches}")

        def analyze_files(files):
            """Analyze files synchronously."""
            analysis: Dict[str, Any] = {
                "file_types": {},
                "total_additions": 0,
                "total_deletions": 0,
                "modified_files": 0,
                "new_files": 0,
                "deleted_files": 0,
                "large_files": [],
                "file_details": [],
            }

            for file_data in files:
                filename = file_data.get("filename", "")
                status = file_data.get("status", "modified")
                additions = file_data.get("additions", 0)
                deletions = file_data.get("deletions", 0)
                changes = file_data.get("changes", 0)

                # File extension analysis
                if "." in filename:
                    ext = filename.split(".")[-1].lower()
                    analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1

                # Status analysis
                if status == "added":
                    analysis["new_files"] += 1
                elif status == "removed":
                    analysis["deleted_files"] += 1
                else:
                    analysis["modified_files"] += 1

                # Size analysis
                analysis["total_additions"] += additions
                analysis["total_deletions"] += deletions

                # Large file detection (>500 changes)
                if changes > 500:
                    analysis["large_files"].append(
                        {
                            "filename": filename,
                            "changes": changes,
                            "additions": additions,
                            "deletions": deletions,
                        }
                    )

                # Store file details
                analysis["file_details"].append(
                    {
                        "filename": filename,
                        "status": status,
                        "additions": additions,
                        "deletions": deletions,
                        "changes": changes,
                    }
                )

            return analysis

        try:
            # Run analysis in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, analyze_files, file_batch)

            logger.debug(f"File batch {batch_number} completed")
            return result

        except Exception as e:
            logger.error(f"Error processing file batch {batch_number}: {e}")
            return {"error": str(e), "batch_number": batch_number}

    async def _process_commit_batch(
        self, commit_batch: List[Dict[str, Any]], batch_number: int, total_batches: int
    ) -> Dict[str, Any]:
        """Process a batch of commits.

        Args:
            commit_batch: Batch of commits to process
            batch_number: Current batch number
            total_batches: Total number of batches

        Returns:
            Batch processing results
        """
        logger.debug(f"Processing commit batch {batch_number}/{total_batches}")

        def analyze_commits(commits):
            """Analyze commits synchronously."""
            analysis: Dict[str, Any] = {
                "commit_count": len(commits),
                "authors": {},
                "commit_messages": [],
                "commit_dates": [],
                "merge_commits": 0,
                "fix_commits": 0,
                "feature_commits": 0,
                "commit_details": [],
            }

            for commit_data in commits:
                commit = commit_data.get("commit", {})
                message = commit.get("message", "")
                author = commit.get("author", {})
                author_name = author.get("name", "Unknown")
                date = commit.get("date", "")

                # Author analysis
                analysis["authors"][author_name] = analysis["authors"].get(author_name, 0) + 1

                # Message analysis
                message_lower = message.lower()
                if "merge" in message_lower:
                    analysis["merge_commits"] += 1
                elif any(word in message_lower for word in ["fix", "bug", "error"]):
                    analysis["fix_commits"] += 1
                elif any(word in message_lower for word in ["feat", "feature", "add"]):
                    analysis["feature_commits"] += 1

                # Store data
                analysis["commit_messages"].append(message)
                analysis["commit_dates"].append(date)
                analysis["commit_details"].append(
                    {
                        "message": message,
                        "author": author_name,
                        "date": date,
                        "sha": commit_data.get("sha", ""),
                    }
                )

            return analysis

        try:
            # Run analysis in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, analyze_commits, commit_batch)

            logger.debug(f"Commit batch {batch_number} completed")
            return result

        except Exception as e:
            logger.error(f"Error processing commit batch {batch_number}: {e}")
            return {"error": str(e), "batch_number": batch_number}

    async def _process_generic_batch(
        self, item_batch: List[Any], processor_func: Callable[[Any], Any]
    ) -> List[Any]:
        """Process a generic batch of items.

        Args:
            item_batch: Batch of items to process
            processor_func: Function to process each item

        Returns:
            List of processed results
        """

        def process_batch(items):
            """Process items synchronously."""
            results = []
            for item in items:
                try:
                    result = processor_func(item)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing item: {e}")
            return results

        # Run processing in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, process_batch, item_batch)

    async def _combine_file_results(
        self, results: List[Union[Dict[str, Any], Exception]]
    ) -> Dict[str, Any]:
        """Combine file analysis results.

        Args:
            results: List of batch results

        Returns:
            Combined analysis
        """

        def combine_sync():
            """Synchronous combination logic."""
            combined = {
                "file_types": {},
                "total_additions": 0,
                "total_deletions": 0,
                "modified_files": 0,
                "new_files": 0,
                "deleted_files": 0,
                "large_files": [],
                "file_details": [],
                "batch_errors": [],
            }

            for result in results:
                if isinstance(result, Exception):
                    combined["batch_errors"].append(str(result))
                    continue

                if isinstance(result, dict) and "error" not in result:
                    # Combine file types
                    for ext, count in result.get("file_types", {}).items():
                        combined["file_types"][ext] = combined["file_types"].get(ext, 0) + count

                    # Sum numeric values
                    combined["total_additions"] += result.get("total_additions", 0)
                    combined["total_deletions"] += result.get("total_deletions", 0)
                    combined["modified_files"] += result.get("modified_files", 0)
                    combined["new_files"] += result.get("new_files", 0)
                    combined["deleted_files"] += result.get("deleted_files", 0)

                    # Extend lists
                    combined["large_files"].extend(result.get("large_files", []))
                    combined["file_details"].extend(result.get("file_details", []))

            return combined

        # Run combination in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, combine_sync)

    async def _combine_commit_results(
        self, results: List[Union[Dict[str, Any], Exception]]
    ) -> Dict[str, Any]:
        """Combine commit analysis results.

        Args:
            results: List of batch results

        Returns:
            Combined analysis
        """

        def combine_sync():
            """Synchronous combination logic."""
            combined = {
                "commit_count": 0,
                "authors": {},
                "commit_messages": [],
                "commit_dates": [],
                "merge_commits": 0,
                "fix_commits": 0,
                "feature_commits": 0,
                "commit_details": [],
                "batch_errors": [],
            }

            for result in results:
                if isinstance(result, Exception):
                    combined["batch_errors"].append(str(result))
                    continue

                if isinstance(result, dict) and "error" not in result:
                    # Sum counts
                    combined["commit_count"] += result.get("commit_count", 0)
                    combined["merge_commits"] += result.get("merge_commits", 0)
                    combined["fix_commits"] += result.get("fix_commits", 0)
                    combined["feature_commits"] += result.get("feature_commits", 0)

                    # Combine authors
                    for author, count in result.get("authors", {}).items():
                        combined["authors"][author] = combined["authors"].get(author, 0) + count

                    # Extend lists
                    combined["commit_messages"].extend(result.get("commit_messages", []))
                    combined["commit_dates"].extend(result.get("commit_dates", []))
                    combined["commit_details"].extend(result.get("commit_details", []))

            return combined

        # Run combination in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, combine_sync)

    async def close(self) -> None:
        """Close the batch processor and cleanup resources."""
        if self.executor:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.executor.shutdown, True)
            logger.info("AsyncBatchProcessor executor shut down")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

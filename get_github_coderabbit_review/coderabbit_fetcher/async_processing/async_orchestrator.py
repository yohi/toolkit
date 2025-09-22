"""Async orchestrator for CodeRabbit fetcher operations."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from ..exceptions import CodeRabbitFetcherError
from ..models import AnalyzedComments
from ..orchestrator import ExecutionConfig
from ..patterns.observer import EventType, publish_event
from .async_batch_processor import AsyncBatchProcessor
from .async_comment_analyzer import AsyncCommentAnalyzer
from .async_github_client import AsyncGitHubClient

logger = logging.getLogger(__name__)


class AsyncCodeRabbitOrchestrator:
    """Async orchestrator for CodeRabbit fetcher operations."""

    def __init__(self, config: ExecutionConfig):
        """Initialize async orchestrator.

        Args:
            config: Execution configuration
        """
        self.config = config
        self.session_id = f"async_{int(time.time())}"

        # Initialize async components
        self.github_client = AsyncGitHubClient()
        self.comment_analyzer = AsyncCommentAnalyzer()
        self.batch_processor = AsyncBatchProcessor()

        # Execution state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Results
        self.results: Dict[str, Any] = {}

    async def execute_async(self) -> Dict[str, Any]:
        """Execute CodeRabbit fetching asynchronously.

        Returns:
            Execution results

        Raises:
            CodeRabbitFetcherError: If execution fails
        """
        self.start_time = datetime.now()
        self.is_running = True

        # Publish start event
        publish_event(
            EventType.PROCESSING_STARTED,
            source="AsyncCodeRabbitOrchestrator",
            data={
                "session_id": self.session_id,
                "pr_url": self.config.pr_url,
                "output_format": self.config.output_format,
                "phase": "initialization",
            },
            session_id=self.session_id,
        )

        try:
            # Execute async pipeline
            results = await self._execute_pipeline()

            self.end_time = datetime.now()
            self.is_running = False

            # Publish completion event
            execution_time = (self.end_time - self.start_time).total_seconds()
            publish_event(
                EventType.PROCESSING_COMPLETED,
                source="AsyncCodeRabbitOrchestrator",
                data={
                    "session_id": self.session_id,
                    "execution_time_seconds": execution_time,
                    "results_summary": self._get_results_summary(results),
                },
                session_id=self.session_id,
            )

            return results

        except Exception as e:
            self.end_time = datetime.now()
            self.is_running = False

            # Publish failure event
            publish_event(
                EventType.PROCESSING_FAILED,
                source="AsyncCodeRabbitOrchestrator",
                data={
                    "session_id": self.session_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                severity="error",
                session_id=self.session_id,
            )

            logger.error(f"Async execution failed: {e}")
            raise CodeRabbitFetcherError(f"Async execution failed: {e}") from e

    async def _execute_pipeline(self) -> Dict[str, Any]:
        """Execute the async processing pipeline."""

        # Stage 1: Validate and fetch PR data
        await self._publish_progress("validation", 0, 6)
        pr_data = await self._validate_and_fetch_pr_data()

        # Stage 2: Fetch GitHub data in parallel
        await self._publish_progress("data_fetching", 1, 6)
        github_data = await self._fetch_github_data_parallel(pr_data)

        # Stage 3: Analyze comments asynchronously
        await self._publish_progress("comment_analysis", 2, 6)
        analyzed_comments = await self._analyze_comments_async(github_data)

        # Stage 4: Process additional data in parallel
        await self._publish_progress("additional_processing", 3, 6)
        additional_data = await self._process_additional_data_parallel(github_data)

        # Stage 5: Format output
        await self._publish_progress("output_formatting", 4, 6)
        formatted_output = await self._format_output_async(analyzed_comments)

        # Stage 6: Finalize results
        await self._publish_progress("finalization", 5, 6)
        results = await self._finalize_results(analyzed_comments, formatted_output, additional_data)

        await self._publish_progress("completed", 6, 6)
        return results

    async def _validate_and_fetch_pr_data(self) -> Dict[str, Any]:
        """Validate configuration and fetch basic PR data."""
        logger.info("Validating PR URL and fetching basic data...")

        # Validate GitHub authentication
        if not await self.github_client.validate_auth_async():
            raise CodeRabbitFetcherError("GitHub authentication failed")

        # Extract PR information
        pr_info = await self.github_client.extract_pr_info_async(self.config.pr_url)

        return {
            "pr_info": pr_info,
            "owner": pr_info["owner"],
            "repo": pr_info["repo"],
            "pr_number": pr_info["number"],
        }

    async def _fetch_github_data_parallel(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch GitHub data in parallel."""
        logger.info("Fetching GitHub data in parallel...")

        owner = pr_data["owner"]
        repo = pr_data["repo"]
        pr_number = pr_data["pr_number"]

        # Create parallel tasks
        tasks = [
            asyncio.create_task(
                self.github_client.get_pr_comments_async(owner, repo, pr_number),
                name="fetch_comments",
            ),
            asyncio.create_task(
                self.github_client.get_pr_reviews_async(owner, repo, pr_number),
                name="fetch_reviews",
            ),
            asyncio.create_task(
                self.github_client.get_pr_files_async(owner, repo, pr_number), name="fetch_files"
            ),
            asyncio.create_task(
                self.github_client.get_pr_commits_async(owner, repo, pr_number),
                name="fetch_commits",
            ),
        ]

        # Execute tasks concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=120  # 2 minutes timeout
            )

            # Process results
            comments, reviews, files, commits = results

            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_name = tasks[i].get_name()
                    logger.error(f"Failed to {task_name}: {result}")
                    # Set default empty result
                    if i == 0:  # comments
                        comments = []
                    elif i == 1:  # reviews
                        reviews = []
                    elif i == 2:  # files
                        files = []
                    elif i == 3:  # commits
                        commits = []

            return {
                "comments": comments or [],
                "reviews": reviews or [],
                "files": files or [],
                "commits": commits or [],
                "pr_info": pr_data["pr_info"],
            }

        except asyncio.TimeoutError:
            logger.error("Timeout while fetching GitHub data")
            # Cancel all pending tasks
            for task in tasks:
                if not task.done():
                    logger.warning(f"Cancelling task: {task.get_name()}")
                    task.cancel()

            # Wait briefly for cancellation to complete
            try:
                await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not cancel within timeout")

            raise CodeRabbitFetcherError("Timeout while fetching GitHub data")

    async def _analyze_comments_async(self, github_data: Dict[str, Any]) -> AnalyzedComments:
        """Analyze comments asynchronously."""
        logger.info("Analyzing comments asynchronously...")

        # Combine all comment sources
        all_comments = []
        all_comments.extend(github_data.get("comments", []))
        all_comments.extend(github_data.get("reviews", []))

        if not all_comments:
            logger.warning("No comments found to analyze")
            return AnalyzedComments(
                summary_comments=[],
                review_comments=[],
                unresolved_threads=[],
                metadata={"total_comments": 0},
            )

        # Analyze comments using async analyzer
        return await self.comment_analyzer.analyze_comments_async(all_comments, batch_size=20)

    async def _process_additional_data_parallel(
        self, github_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process additional data in parallel."""
        logger.info("Processing additional data...")

        files = github_data.get("files", [])
        commits = github_data.get("commits", [])

        # Create parallel processing tasks
        tasks = []

        if files:
            tasks.append(
                asyncio.create_task(
                    self.batch_processor.process_files_async(files), name="process_files"
                )
            )

        if commits:
            tasks.append(
                asyncio.create_task(
                    self.batch_processor.process_commits_async(commits), name="process_commits"
                )
            )

        if not tasks:
            return {"file_analysis": {}, "commit_analysis": {}}

        # Execute tasks
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            file_analysis = {}
            commit_analysis = {}

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_name = tasks[i].get_name()
                    logger.error(f"Failed to {task_name}: {result}")
                else:
                    if tasks[i].get_name() == "process_files":
                        file_analysis = result
                    elif tasks[i].get_name() == "process_commits":
                        commit_analysis = result

            return {"file_analysis": file_analysis, "commit_analysis": commit_analysis}

        except Exception as e:
            logger.error(f"Error processing additional data: {e}")
            return {"file_analysis": {}, "commit_analysis": {}}

    async def _format_output_async(self, analyzed_comments: AnalyzedComments) -> str:
        """Format output asynchronously."""
        logger.info(f"Formatting output as {self.config.output_format}...")

        # Use async formatting if available, otherwise fallback to sync
        try:
            from ..formatters import get_formatter

            formatter = get_formatter(self.config.output_format)

            # Check if formatter has async support
            if hasattr(formatter, "format_async"):
                return await formatter.format_async(analyzed_comments)
            else:
                # Run sync formatter in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, formatter.format, analyzed_comments)

        except Exception as e:
            logger.error(f"Error formatting output: {e}")
            # Fallback to simple text output
            return f"Error formatting output: {e}"

    async def _finalize_results(
        self,
        analyzed_comments: AnalyzedComments,
        formatted_output: str,
        additional_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Finalize execution results."""

        execution_time = ((self.end_time or datetime.now()) - self.start_time).total_seconds()

        results = {
            "success": True,
            "session_id": self.session_id,
            "execution_time_seconds": execution_time,
            "output": formatted_output,
            "analyzed_comments": analyzed_comments,
            "additional_data": additional_data,
            "metadata": {
                "pr_url": self.config.pr_url,
                "output_format": self.config.output_format,
                "total_comments": len(analyzed_comments.review_comments),
                "summary_comments": len(analyzed_comments.summary_comments),
                "unresolved_threads": len(analyzed_comments.unresolved_threads),
                "processing_mode": "async",
                "start_time": self.start_time.isoformat(),
                "end_time": (self.end_time or datetime.now()).isoformat(),
            },
        }

        self.results = results
        return results

    async def _publish_progress(self, phase: str, current: int, total: int) -> None:
        """Publish progress update event."""
        progress_percent = (current / total) * 100 if total > 0 else 0

        publish_event(
            EventType.PROGRESS_UPDATE,
            source="AsyncCodeRabbitOrchestrator",
            data={
                "session_id": self.session_id,
                "phase": phase,
                "current_step": current,
                "total_steps": total,
                "progress_percent": progress_percent,
            },
            session_id=self.session_id,
        )

        logger.debug(f"Progress: {phase} ({current}/{total} - {progress_percent:.1f}%)")

    def _get_results_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of results for events."""
        return {
            "success": results.get("success", False),
            "execution_time_seconds": results.get("execution_time_seconds", 0),
            "total_comments": results.get("metadata", {}).get("total_comments", 0),
            "output_format": self.config.output_format,
        }

    async def cancel_execution(self) -> None:
        """Cancel ongoing execution."""
        if self.is_running:
            logger.info("Cancelling async execution...")
            self.is_running = False

            # Cancel GitHub client operations
            await self.github_client.cancel_operations()

            # Publish cancellation event
            publish_event(
                EventType.PROCESSING_FAILED,
                source="AsyncCodeRabbitOrchestrator",
                data={
                    "session_id": self.session_id,
                    "error": "Execution cancelled by user",
                    "error_type": "CancellationError",
                },
                severity="warning",
                session_id=self.session_id,
            )

    def get_current_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        if not self.start_time:
            return {"status": "not_started"}

        if self.is_running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            return {
                "status": "running",
                "session_id": self.session_id,
                "elapsed_seconds": elapsed,
                "start_time": self.start_time.isoformat(),
            }

        return {
            "status": "completed" if self.results.get("success") else "failed",
            "session_id": self.session_id,
            "results": self.results,
        }


async def execute_async_coderabbit_fetcher(config: ExecutionConfig) -> Dict[str, Any]:
    """Convenience function to execute async CodeRabbit fetcher.

    Args:
        config: Execution configuration

    Returns:
        Execution results
    """
    orchestrator = AsyncCodeRabbitOrchestrator(config)
    return await orchestrator.execute_async()

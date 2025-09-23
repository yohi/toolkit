"""Async task manager for CodeRabbit fetcher."""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AsyncTask:
    """Async task definition."""

    id: str
    name: str
    coroutine: Coroutine
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: Optional[int] = None
    retry_attempts: int = 0
    max_retries: int = 0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Runtime information
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Any = None


class AsyncTaskManager:
    """Manager for async task execution with dependencies, priorities, and retries."""

    def __init__(self, max_concurrent_tasks: int = 10):
        """Initialize async task manager.

        Args:
            max_concurrent_tasks: Maximum number of concurrent tasks
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Task storage
        self.tasks: Dict[str, AsyncTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # Event hooks
        self.task_started_hooks: List[Callable[[AsyncTask], None]] = []
        self.task_completed_hooks: List[Callable[[AsyncTask], None]] = []
        self.task_failed_hooks: List[Callable[[AsyncTask, str], None]] = []

        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "total_execution_time": 0.0,
        }

    def add_task(
        self,
        name: str,
        coroutine: Coroutine,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 0,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a task to the manager.

        Args:
            name: Task name
            coroutine: Coroutine to execute
            priority: Task priority
            timeout_seconds: Execution timeout
            max_retries: Maximum retry attempts
            dependencies: List of task IDs this task depends on
            metadata: Additional task metadata

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        task = AsyncTask(
            id=task_id,
            name=name,
            coroutine=coroutine,
            priority=priority,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        self.tasks[task_id] = task
        self.stats["total_tasks"] += 1

        logger.debug(f"Added task {name} with ID {task_id}")
        return task_id

    def add_task_group(self, task_definitions: List[Dict[str, Any]]) -> List[str]:
        """Add multiple tasks as a group.

        Args:
            task_definitions: List of task definition dictionaries

        Returns:
            List of task IDs
        """
        task_ids = []

        for task_def in task_definitions:
            task_id = self.add_task(
                name=task_def["name"],
                coroutine=task_def["coroutine"],
                priority=task_def.get("priority", TaskPriority.NORMAL),
                timeout_seconds=task_def.get("timeout_seconds"),
                max_retries=task_def.get("max_retries", 0),
                dependencies=task_def.get("dependencies"),
                metadata=task_def.get("metadata"),
            )
            task_ids.append(task_id)

        logger.info(f"Added task group with {len(task_ids)} tasks")
        return task_ids

    async def execute_all_tasks(self) -> Dict[str, Any]:
        """Execute all tasks respecting dependencies and priorities.

        Returns:
            Execution summary
        """
        start_time = time.time()

        logger.info(f"Starting execution of {len(self.tasks)} tasks")

        try:
            # Create execution plan
            execution_plan = self._create_execution_plan()

            # Execute tasks in waves
            for wave_number, task_ids in enumerate(execution_plan):
                logger.info(f"Executing wave {wave_number + 1} with {len(task_ids)} tasks")
                await self._execute_task_wave(task_ids)

            execution_time = time.time() - start_time
            self.stats["total_execution_time"] = execution_time

            # Generate summary
            summary = self._generate_execution_summary()
            summary["execution_time_seconds"] = execution_time

            logger.info(f"All tasks completed in {execution_time:.2f}s")
            return summary

        except Exception as e:
            logger.error(f"Error executing tasks: {e}")
            raise

    async def execute_task(self, task_id: str) -> Any:
        """Execute a single task.

        Args:
            task_id: Task ID to execute

        Returns:
            Task result

        Raises:
            ValueError: If task not found
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]

        # Check dependencies
        if not self._dependencies_satisfied(task):
            unmet_deps = [
                dep for dep in task.dependencies if self.tasks[dep].status != TaskStatus.COMPLETED
            ]
            raise ValueError(f"Task {task_id} has unmet dependencies: {unmet_deps}")

        return await self._execute_single_task(task)

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for a specific task to complete.

        Args:
            task_id: Task ID to wait for
            timeout: Wait timeout in seconds

        Returns:
            Task result
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]

        # If task is already completed
        if task.status == TaskStatus.COMPLETED:
            return task.result

        # If task failed
        if task.status == TaskStatus.FAILED:
            raise RuntimeError(f"Task {task_id} failed: {task.error}")

        # Wait for running task
        if task_id in self.running_tasks:
            try:
                return await asyncio.wait_for(self.running_tasks[task_id], timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout}s") from None

        # Task is pending, execute it
        return await self.execute_task(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if task was cancelled
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        # Cancel running task
        if task_id in self.running_tasks:
            running_task = self.running_tasks[task_id]
            running_task.cancel()

            try:
                await running_task
            except asyncio.CancelledError:
                pass

            del self.running_tasks[task_id]

        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        self.stats["cancelled_tasks"] += 1

        logger.info(f"Cancelled task {task.name} ({task_id})")
        return True

    async def cancel_all_tasks(self) -> int:
        """Cancel all pending and running tasks.

        Returns:
            Number of tasks cancelled
        """
        cancelled_count = 0

        # Get all task IDs to avoid modification during iteration
        task_ids = list(self.tasks.keys())

        for task_id in task_ids:
            task = self.tasks[task_id]
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                if await self.cancel_task(task_id):
                    cancelled_count += 1

        logger.info(f"Cancelled {cancelled_count} tasks")
        return cancelled_count

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status.

        Args:
            task_id: Task ID

        Returns:
            Task status or None if not found
        """
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None

    def get_all_task_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tasks.

        Returns:
            Dictionary mapping task IDs to status information
        """
        statuses = {}

        for task_id, task in self.tasks.items():
            statuses[task_id] = {
                "name": task.name,
                "status": task.status.value,
                "priority": task.priority.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.error,
                "retry_attempts": task.retry_attempts,
                "dependencies": task.dependencies,
                "metadata": task.metadata,
            }

        return statuses

    def add_task_started_hook(self, hook: Callable[[AsyncTask], None]) -> None:
        """Add a hook for task started events."""
        self.task_started_hooks.append(hook)

    def add_task_completed_hook(self, hook: Callable[[AsyncTask], None]) -> None:
        """Add a hook for task completed events."""
        self.task_completed_hooks.append(hook)

    def add_task_failed_hook(self, hook: Callable[[AsyncTask, str], None]) -> None:
        """Add a hook for task failed events."""
        self.task_failed_hooks.append(hook)

    def _create_execution_plan(self) -> List[List[str]]:
        """Create execution plan with dependency resolution.

        Returns:
            List of waves, each containing task IDs that can be executed in parallel
        """
        # Topological sort for dependency resolution
        remaining_tasks = dict(self.tasks)
        execution_waves = []

        while remaining_tasks:
            # Find tasks with no unmet dependencies
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                if self._dependencies_satisfied(
                    task, completed_tasks=set(self.tasks.keys()) - set(remaining_tasks.keys())
                ):
                    ready_tasks.append(task_id)

            if not ready_tasks:
                # Check if we have failed/cancelled dependencies blocking progress
                blocked_by_failed = []
                for task_id, task in remaining_tasks.items():
                    for dep_id in task.dependencies:
                        if dep_id in self.tasks:
                            dep_task = self.tasks[dep_id]
                            if dep_task.status in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
                                blocked_by_failed.append((task_id, dep_id, dep_task.status))

                if blocked_by_failed:
                    # Tasks blocked by failed dependencies
                    error_msg = "Tasks blocked by failed dependencies:"
                    for task_id, dep_id, status in blocked_by_failed:
                        error_msg += f"\n- {task_id} blocked by {dep_id} ({status.value})"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                else:
                    # True circular dependency
                    unresolved = list(remaining_tasks.keys())
                    logger.error(f"Circular dependency detected in tasks: {unresolved}")
                    raise ValueError(f"Circular dependency detected in tasks: {unresolved}")

            # Sort by priority (highest first)
            ready_tasks.sort(key=lambda tid: self.tasks[tid].priority.value, reverse=True)
            execution_waves.append(ready_tasks)

            # Remove ready tasks from remaining
            for task_id in ready_tasks:
                del remaining_tasks[task_id]

        return execution_waves

    def _dependencies_satisfied(
        self, task: AsyncTask, completed_tasks: Optional[set] = None
    ) -> bool:
        """Check if task dependencies are satisfied.

        Args:
            task: Task to check
            completed_tasks: Set of completed task IDs

        Returns:
            True if all dependencies are satisfied
        """
        if not task.dependencies:
            return True

        if completed_tasks is None:
            completed_tasks = {
                task_id for task_id, t in self.tasks.items() if t.status == TaskStatus.COMPLETED
            }

        # Check each dependency
        for dep_id in task.dependencies:
            # Dependency must exist
            if dep_id not in self.tasks:
                logger.error(f"Task {task.task_id} depends on non-existent task {dep_id}")
                return False

            # Dependency must be completed
            if dep_id not in completed_tasks:
                dep_task = self.tasks[dep_id]
                # If dependency failed or was cancelled, this task cannot proceed
                if dep_task.status in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    logger.error(
                        f"Task {task.task_id} cannot proceed: dependency {dep_id} {dep_task.status.value}"
                    )
                    return False
                # Otherwise, dependency is just not complete yet
                return False

        return True

    async def _execute_task_wave(self, task_ids: List[str]) -> None:
        """Execute a wave of tasks in parallel.

        Args:
            task_ids: List of task IDs to execute
        """
        tasks_to_run = [self._execute_single_task(self.tasks[task_id]) for task_id in task_ids]

        if tasks_to_run:
            await asyncio.gather(*tasks_to_run, return_exceptions=True)

    async def _execute_single_task(self, task: AsyncTask) -> Any:
        """Execute a single task with retries and error handling.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        async with self.semaphore:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            # Call started hooks
            for hook in self.task_started_hooks:
                try:
                    hook(task)
                except Exception as e:
                    logger.warning(f"Task started hook failed: {e}")

            logger.debug(f"Starting task {task.name} ({task.id})")

            # Create asyncio task for execution
            execution_task = asyncio.create_task(task.coroutine)
            self.running_tasks[task.id] = execution_task

            try:
                # Execute with timeout
                if task.timeout_seconds:
                    result = await asyncio.wait_for(execution_task, timeout=task.timeout_seconds)
                else:
                    result = await execution_task

                # Task completed successfully
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                self.stats["completed_tasks"] += 1

                # Call completed hooks
                for hook in self.task_completed_hooks:
                    try:
                        hook(task)
                    except Exception as e:
                        logger.warning(f"Task completed hook failed: {e}")

                logger.debug(f"Completed task {task.name} ({task.id})")
                return result

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Task {task.name} failed: {error_msg}")

                # Handle retries
                if task.retry_attempts < task.max_retries:
                    task.retry_attempts += 1
                    logger.info(
                        f"Retrying task {task.name} (attempt {task.retry_attempts}/{task.max_retries})"
                    )

                    # Reset status for retry
                    task.status = TaskStatus.PENDING
                    task.started_at = None

                    # Wait a bit before retry
                    await asyncio.sleep(min(2**task.retry_attempts, 10))  # Exponential backoff

                    # Recursive retry
                    return await self._execute_single_task(task)

                # Task failed permanently
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error = error_msg
                self.stats["failed_tasks"] += 1

                # Call failed hooks
                for hook in self.task_failed_hooks:
                    try:
                        hook(task, error_msg)
                    except Exception as hook_error:
                        logger.warning(f"Task failed hook failed: {hook_error}")

                raise

            finally:
                # Clean up running task reference
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]

    def _generate_execution_summary(self) -> Dict[str, Any]:
        """Generate execution summary.

        Returns:
            Execution summary
        """
        summary = {
            "total_tasks": self.stats["total_tasks"],
            "completed_tasks": self.stats["completed_tasks"],
            "failed_tasks": self.stats["failed_tasks"],
            "cancelled_tasks": self.stats["cancelled_tasks"],
            "success_rate": 0.0,
        }

        if self.stats["total_tasks"] > 0:
            summary["success_rate"] = self.stats["completed_tasks"] / self.stats["total_tasks"]

        # Task breakdown by status
        status_counts: dict[str, int] = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        summary["status_breakdown"] = status_counts

        # Priority breakdown
        priority_counts: dict[str, int] = {}
        for task in self.tasks.values():
            priority = task.priority.value
            priority_counts[f"priority_{priority}"] = (
                priority_counts.get(f"priority_{priority}", 0) + 1
            )

        summary["priority_breakdown"] = priority_counts

        return summary

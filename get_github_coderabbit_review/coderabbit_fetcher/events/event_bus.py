"""Event bus implementation for CodeRabbit fetcher."""

import asyncio
import inspect
import logging
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Union

from ..patterns.observer import Event, EventType

logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Abstract event handler."""

    @abstractmethod
    def handle(self, event: Event) -> Any:
        """Handle event synchronously.

        Args:
            event: Event to handle

        Returns:
            Handler result
        """
        pass

    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type.

        Args:
            event_type: Event type to check

        Returns:
            True if handler can handle the event type
        """
        pass


class AsyncEventHandler(ABC):
    """Abstract async event handler."""

    @abstractmethod
    async def handle_async(self, event: Event) -> Any:
        """Handle event asynchronously.

        Args:
            event: Event to handle

        Returns:
            Handler result
        """
        pass

    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type.

        Args:
            event_type: Event type to check

        Returns:
            True if handler can handle the event type
        """
        pass


class EventMiddleware(ABC):
    """Abstract event middleware."""

    @abstractmethod
    def before_handle(self, event: Event) -> Event:
        """Process event before handling.

        Args:
            event: Event to process

        Returns:
            Processed event
        """
        pass

    @abstractmethod
    def after_handle(self, event: Event, result: Any) -> Any:
        """Process result after handling.

        Args:
            event: Original event
            result: Handler result

        Returns:
            Processed result
        """
        pass

    @abstractmethod
    def on_error(self, event: Event, error: Exception) -> None:
        """Handle errors during event processing.

        Args:
            event: Event that caused error
            error: Exception that occurred
        """
        pass


@dataclass
class HandlerRegistration:
    """Handler registration information."""

    handler: Union[EventHandler, AsyncEventHandler, Callable]
    event_types: List[EventType]
    priority: int = 0
    is_async: bool = False
    metadata: Dict[str, Any] = None


class FunctionEventHandler(EventHandler):
    """Wrapper for function-based event handlers."""

    def __init__(self, func: Callable[[Event], Any], event_types: List[EventType]):
        """Initialize function event handler.

        Args:
            func: Handler function
            event_types: Event types this handler can handle
        """
        self.func = func
        self.event_types = set(event_types)

    def handle(self, event: Event) -> Any:
        """Handle event using function."""
        return self.func(event)

    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        return event_type in self.event_types


class AsyncFunctionEventHandler(AsyncEventHandler):
    """Wrapper for async function-based event handlers."""

    def __init__(self, func: Callable[[Event], Any], event_types: List[EventType]):
        """Initialize async function event handler.

        Args:
            func: Async handler function
            event_types: Event types this handler can handle
        """
        self.func = func
        self.event_types = set(event_types)

    async def handle_async(self, event: Event) -> Any:
        """Handle event using async function."""
        return await self.func(event)

    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        return event_type in self.event_types


class LoggingMiddleware(EventMiddleware):
    """Middleware for logging events."""

    def __init__(self, log_level: int = logging.INFO):
        """Initialize logging middleware.

        Args:
            log_level: Logging level
        """
        self.log_level = log_level
        self.logger = logging.getLogger(f"{__name__}.LoggingMiddleware")

    def before_handle(self, event: Event) -> Event:
        """Log event before handling."""
        self.logger.log(
            self.log_level, f"Processing event: {event.event_type.value} from {event.source}"
        )
        return event

    def after_handle(self, event: Event, result: Any) -> Any:
        """Log result after handling."""
        self.logger.log(
            self.log_level,
            f"Completed event: {event.event_type.value} (result: {type(result).__name__})",
        )
        return result

    def on_error(self, event: Event, error: Exception) -> None:
        """Log errors."""
        self.logger.error(
            f"Error processing event {event.event_type.value}: {error}", exc_info=True
        )


class TimingMiddleware(EventMiddleware):
    """Middleware for timing event processing."""

    def __init__(self):
        """Initialize timing middleware."""
        self._start_times: Dict[str, float] = {}

    def before_handle(self, event: Event) -> Event:
        """Record start time."""
        event_id = id(event)
        self._start_times[event_id] = time.time()
        return event

    def after_handle(self, event: Event, result: Any) -> Any:
        """Record completion time."""
        event_id = id(event)
        if event_id in self._start_times:
            duration = time.time() - self._start_times[event_id]
            del self._start_times[event_id]

            # Add timing info to event metadata
            if hasattr(event, "data"):
                event.data["processing_time_ms"] = duration * 1000

            logger.debug(f"Event {event.event_type.value} processed in {duration:.3f}s")

        return result

    def on_error(self, event: Event, error: Exception) -> None:
        """Clean up timing info on error."""
        event_id = id(event)
        if event_id in self._start_times:
            del self._start_times[event_id]


class EventBus:
    """Event bus for decoupled event handling."""

    def __init__(self, max_workers: int = 4):
        """Initialize event bus.

        Args:
            max_workers: Maximum number of worker threads for async processing
        """
        self.max_workers = max_workers
        self._handlers: List[HandlerRegistration] = []
        self._middleware: List[EventMiddleware] = []
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()

        # Statistics
        self.stats = {
            "events_processed": 0,
            "events_failed": 0,
            "total_processing_time": 0.0,
            "handlers_registered": 0,
        }

        # Add default middleware
        self.add_middleware(TimingMiddleware())

    def register_handler(
        self,
        handler: Union[EventHandler, AsyncEventHandler, Callable],
        event_types: List[EventType],
        priority: int = 0,
        is_async: bool = None,
    ) -> None:
        """Register event handler.

        Args:
            handler: Event handler
            event_types: Event types to handle
            priority: Handler priority (higher = earlier execution)
            is_async: Whether handler is async (auto-detected if None)
        """
        with self._lock:
            # Auto-detect async
            if is_async is None:
                if isinstance(handler, AsyncEventHandler):
                    is_async = True
                elif isinstance(handler, EventHandler):
                    is_async = False
                elif callable(handler):
                    is_async = inspect.iscoroutinefunction(handler)
                else:
                    is_async = False

            # Wrap function handlers
            if callable(handler) and not isinstance(handler, (EventHandler, AsyncEventHandler)):
                if is_async:
                    handler = AsyncFunctionEventHandler(handler, event_types)
                else:
                    handler = FunctionEventHandler(handler, event_types)

            registration = HandlerRegistration(
                handler=handler, event_types=event_types, priority=priority, is_async=is_async
            )

            self._handlers.append(registration)

            # Sort by priority (higher priority first)
            self._handlers.sort(key=lambda r: r.priority, reverse=True)

            self.stats["handlers_registered"] += 1
            logger.debug(f"Registered handler for {len(event_types)} event types")

    def add_middleware(self, middleware: EventMiddleware) -> None:
        """Add event middleware.

        Args:
            middleware: Middleware to add
        """
        with self._lock:
            self._middleware.append(middleware)
            logger.debug(f"Added middleware: {type(middleware).__name__}")

    def publish(self, event: Event) -> List[Any]:
        """Publish event synchronously.

        Args:
            event: Event to publish

        Returns:
            List of handler results
        """
        with self._lock:
            start_time = time.time()
            results = []

            try:
                # Apply middleware - before
                processed_event = event
                for middleware in self._middleware:
                    try:
                        processed_event = middleware.before_handle(processed_event)
                    except Exception as e:
                        logger.error(f"Middleware before_handle error: {e}")

                # Find matching handlers
                matching_handlers = [
                    reg
                    for reg in self._handlers
                    if any(
                        reg.handler.can_handle(event_type)
                        for event_type in [processed_event.event_type]
                    )
                ]

                # Execute handlers
                for registration in matching_handlers:
                    try:
                        if registration.is_async:
                            # Run async handler in thread pool
                            future = self._executor.submit(
                                self._run_async_handler, registration.handler, processed_event
                            )
                            result = future.result(timeout=30)  # 30 second timeout
                        else:
                            # Run sync handler
                            result = registration.handler.handle(processed_event)

                        # Apply middleware - after
                        for middleware in self._middleware:
                            try:
                                result = middleware.after_handle(processed_event, result)
                            except Exception as e:
                                logger.error(f"Middleware after_handle error: {e}")

                        results.append(result)

                    except Exception as e:
                        # Apply middleware - error
                        for middleware in self._middleware:
                            try:
                                middleware.on_error(processed_event, e)
                            except Exception as middleware_error:
                                logger.error(f"Middleware on_error error: {middleware_error}")

                        logger.error(f"Handler error for {event.event_type.value}: {e}")
                        self.stats["events_failed"] += 1

                self.stats["events_processed"] += 1
                processing_time = time.time() - start_time
                self.stats["total_processing_time"] += processing_time

                return results

            except Exception as e:
                logger.error(f"Event bus error: {e}")
                self.stats["events_failed"] += 1
                return []

    async def publish_async(self, event: Event) -> List[Any]:
        """Publish event asynchronously.

        Args:
            event: Event to publish

        Returns:
            List of handler results
        """
        start_time = time.time()
        results = []

        try:
            # Apply middleware - before
            processed_event = event
            for middleware in self._middleware:
                try:
                    processed_event = middleware.before_handle(processed_event)
                except Exception as e:
                    logger.error(f"Middleware before_handle error: {e}")

            # Find matching handlers
            matching_handlers = [
                reg
                for reg in self._handlers
                if any(
                    reg.handler.can_handle(event_type)
                    for event_type in [processed_event.event_type]
                )
            ]

            # Execute handlers concurrently
            handler_tasks = []
            for registration in matching_handlers:
                if registration.is_async:
                    task = asyncio.create_task(registration.handler.handle_async(processed_event))
                    handler_tasks.append(task)
                else:
                    # Run sync handler in thread pool
                    loop = asyncio.get_event_loop()
                    task = loop.run_in_executor(
                        self._executor, registration.handler.handle, processed_event
                    )
                    handler_tasks.append(task)

            # Wait for all handlers to complete
            if handler_tasks:
                handler_results = await asyncio.gather(*handler_tasks, return_exceptions=True)

                # Process results and errors
                for result in handler_results:
                    if isinstance(result, Exception):
                        # Apply middleware - error
                        for middleware in self._middleware:
                            try:
                                middleware.on_error(processed_event, result)
                            except Exception as middleware_error:
                                logger.error(f"Middleware on_error error: {middleware_error}")

                        logger.error(f"Async handler error for {event.event_type.value}: {result}")
                        self.stats["events_failed"] += 1
                    else:
                        # Apply middleware - after
                        for middleware in self._middleware:
                            try:
                                result = middleware.after_handle(processed_event, result)
                            except Exception as e:
                                logger.error(f"Middleware after_handle error: {e}")

                        results.append(result)

            self.stats["events_processed"] += 1
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time

            return results

        except Exception as e:
            logger.error(f"Async event bus error: {e}")
            self.stats["events_failed"] += 1
            return []

    def _run_async_handler(self, handler: AsyncEventHandler, event: Event) -> Any:
        """Run async handler in new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(handler.handle_async(event))
        finally:
            loop.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()

        # Calculate additional metrics
        if stats["events_processed"] > 0:
            stats["average_processing_time"] = (
                stats["total_processing_time"] / stats["events_processed"]
            )
            stats["success_rate"] = (stats["events_processed"] - stats["events_failed"]) / stats[
                "events_processed"
            ]
        else:
            stats["average_processing_time"] = 0.0
            stats["success_rate"] = 0.0

        stats["registered_handlers"] = len(self._handlers)
        stats["middleware_count"] = len(self._middleware)

        return stats

    def clear_handlers(self) -> None:
        """Clear all registered handlers."""
        with self._lock:
            self._handlers.clear()
            logger.info("Cleared all event handlers")

    def shutdown(self) -> None:
        """Shutdown event bus and cleanup resources."""
        self._executor.shutdown(wait=True)
        logger.info("Event bus shut down")


# Global event bus instance
_global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus.

    Returns:
        Global event bus instance
    """
    return _global_event_bus


def set_event_bus(event_bus: EventBus) -> None:
    """Set the global event bus.

    Args:
        event_bus: Event bus to set as global
    """
    global _global_event_bus
    _global_event_bus = event_bus


def event_handler(*event_types: EventType, priority: int = 0):
    """Decorator for registering event handlers.

    Args:
        *event_types: Event types to handle
        priority: Handler priority

    Returns:
        Decorator function
    """

    def decorator(func: Callable[[Event], Any]) -> Callable:
        event_bus = get_event_bus()
        event_bus.register_handler(func, list(event_types), priority=priority, is_async=False)
        return func

    return decorator


def async_event_handler(*event_types: EventType, priority: int = 0):
    """Decorator for registering async event handlers.

    Args:
        *event_types: Event types to handle
        priority: Handler priority

    Returns:
        Decorator function
    """

    def decorator(func: Callable[[Event], Any]) -> Callable:
        event_bus = get_event_bus()
        event_bus.register_handler(func, list(event_types), priority=priority, is_async=True)
        return func

    return decorator

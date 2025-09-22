"""Observer pattern implementations for CodeRabbit fetcher."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import threading
import queue
import time

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event type enumeration."""
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"
    PROGRESS_UPDATE = "progress_update"
    MEMORY_WARNING = "memory_warning"
    PERFORMANCE_WARNING = "performance_warning"
    QUALITY_CHECK_FAILED = "quality_check_failed"
    COMPONENT_CREATED = "component_created"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


@dataclass
class Event:
    """Event data structure."""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
            'severity': self.severity,
            'session_id': self.session_id
        }


class EventObserver(ABC):
    """Abstract base class for event observers."""

    @abstractmethod
    def update(self, event: Event) -> None:
        """Handle event notification.

        Args:
            event: Event to handle
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get observer name."""
        pass

    def is_interested_in(self, event_type: EventType) -> bool:
        """Check if observer is interested in event type.

        Args:
            event_type: Type of event

        Returns:
            True if observer should be notified
        """
        return True  # Default: interested in all events


class LoggingObserver(EventObserver):
    """Observer that logs events."""

    def __init__(self, log_level: str = "INFO"):
        """Initialize logging observer.

        Args:
            log_level: Logging level for events
        """
        self.log_level = getattr(logging, log_level.upper())
        self.logger = logging.getLogger(f"{__name__}.LoggingObserver")

    def update(self, event: Event) -> None:
        """Log the event."""
        message = f"[{event.event_type.value}] {event.source}: {event.data}"

        if event.severity == "error":
            self.logger.error(message)
        elif event.severity == "warning":
            self.logger.warning(message)
        else:
            self.logger.log(self.log_level, message)

    def get_name(self) -> str:
        return "LoggingObserver"


class ProgressObserver(EventObserver):
    """Observer that tracks processing progress."""

    def __init__(self):
        """Initialize progress observer."""
        self.progress_data: Dict[str, Dict[str, Any]] = {}
        self.session_start_times: Dict[str, datetime] = {}

    def update(self, event: Event) -> None:
        """Update progress tracking."""
        session_id = event.session_id or "default"

        if event.event_type == EventType.PROCESSING_STARTED:
            self.session_start_times[session_id] = event.timestamp
            self.progress_data[session_id] = {
                'started_at': event.timestamp,
                'total_items': event.data.get('total_items', 0),
                'processed_items': 0,
                'current_phase': event.data.get('phase', 'unknown'),
                'status': 'running'
            }

        elif event.event_type == EventType.PROGRESS_UPDATE:
            if session_id in self.progress_data:
                self.progress_data[session_id].update({
                    'processed_items': event.data.get('processed_items', 0),
                    'current_phase': event.data.get('phase', 'unknown'),
                    'last_update': event.timestamp
                })

        elif event.event_type == EventType.PROCESSING_COMPLETED:
            if session_id in self.progress_data:
                self.progress_data[session_id].update({
                    'completed_at': event.timestamp,
                    'status': 'completed',
                    'final_results': event.data
                })

        elif event.event_type == EventType.PROCESSING_FAILED:
            if session_id in self.progress_data:
                self.progress_data[session_id].update({
                    'failed_at': event.timestamp,
                    'status': 'failed',
                    'error': event.data.get('error', 'Unknown error')
                })

    def get_progress(self, session_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get progress for session.

        Args:
            session_id: Session identifier

        Returns:
            Progress data or None if session not found
        """
        if session_id not in self.progress_data:
            return None

        progress = self.progress_data[session_id].copy()

        # Calculate additional metrics
        if 'started_at' in progress:
            elapsed = datetime.now() - progress['started_at']
            progress['elapsed_seconds'] = elapsed.total_seconds()

            total_items = progress.get('total_items', 0)
            processed_items = progress.get('processed_items', 0)

            if total_items > 0:
                progress['progress_percent'] = (processed_items / total_items) * 100

                if processed_items > 0 and elapsed.total_seconds() > 0:
                    items_per_second = processed_items / elapsed.total_seconds()
                    remaining_items = total_items - processed_items
                    if items_per_second > 0:
                        eta_seconds = remaining_items / items_per_second
                        progress['eta_seconds'] = eta_seconds

        return progress

    def get_name(self) -> str:
        return "ProgressObserver"

    def is_interested_in(self, event_type: EventType) -> bool:
        return event_type in [
            EventType.PROCESSING_STARTED,
            EventType.PROCESSING_COMPLETED,
            EventType.PROCESSING_FAILED,
            EventType.PROGRESS_UPDATE
        ]


class PerformanceObserver(EventObserver):
    """Observer that monitors performance metrics."""

    def __init__(self):
        """Initialize performance observer."""
        self.metrics: Dict[str, List[float]] = {
            'processing_times': [],
            'memory_usage': [],
            'error_rates': []
        }
        self.warnings: List[Dict[str, Any]] = []

    def update(self, event: Event) -> None:
        """Update performance metrics."""
        if event.event_type == EventType.PROCESSING_COMPLETED:
            processing_time = event.data.get('processing_time_seconds', 0)
            if processing_time > 0:
                self.metrics['processing_times'].append(processing_time)

                # Warn about slow processing
                if processing_time > 30:  # More than 30 seconds
                    self.warnings.append({
                        'timestamp': event.timestamp,
                        'type': 'slow_processing',
                        'value': processing_time,
                        'source': event.source
                    })

        elif event.event_type == EventType.MEMORY_WARNING:
            memory_usage = event.data.get('memory_mb', 0)
            if memory_usage > 0:
                self.metrics['memory_usage'].append(memory_usage)
                self.warnings.append({
                    'timestamp': event.timestamp,
                    'type': 'high_memory_usage',
                    'value': memory_usage,
                    'source': event.source
                })

        elif event.event_type == EventType.PROCESSING_FAILED:
            self.metrics['error_rates'].append(1)
            self.warnings.append({
                'timestamp': event.timestamp,
                'type': 'processing_error',
                'error': event.data.get('error', 'Unknown'),
                'source': event.source
            })

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}

        # Processing time statistics
        if self.metrics['processing_times']:
            times = self.metrics['processing_times']
            summary['processing_times'] = {
                'count': len(times),
                'average': sum(times) / len(times),
                'min': min(times),
                'max': max(times),
                'last_10_average': sum(times[-10:]) / min(len(times), 10)
            }

        # Memory usage statistics
        if self.metrics['memory_usage']:
            memory = self.metrics['memory_usage']
            summary['memory_usage'] = {
                'count': len(memory),
                'average': sum(memory) / len(memory),
                'max': max(memory),
                'latest': memory[-1] if memory else 0
            }

        # Error rate
        total_operations = len(self.metrics['processing_times']) + len(self.metrics['error_rates'])
        if total_operations > 0:
            error_rate = len(self.metrics['error_rates']) / total_operations
            summary['error_rate'] = error_rate

        # Recent warnings
        summary['recent_warnings'] = self.warnings[-5:]  # Last 5 warnings
        summary['total_warnings'] = len(self.warnings)

        return summary

    def get_name(self) -> str:
        return "PerformanceObserver"

    def is_interested_in(self, event_type: EventType) -> bool:
        return event_type in [
            EventType.PROCESSING_COMPLETED,
            EventType.PROCESSING_FAILED,
            EventType.MEMORY_WARNING,
            EventType.PERFORMANCE_WARNING
        ]


class QualityObserver(EventObserver):
    """Observer that monitors code quality metrics."""

    def __init__(self):
        """Initialize quality observer."""
        self.quality_metrics: Dict[str, List[float]] = {
            'quality_scores': [],
            'complexity_scores': [],
            'maintainability_scores': []
        }
        self.quality_failures: List[Dict[str, Any]] = []

    def update(self, event: Event) -> None:
        """Update quality metrics."""
        if event.event_type == EventType.QUALITY_CHECK_FAILED:
            self.quality_failures.append({
                'timestamp': event.timestamp,
                'source': event.source,
                'reason': event.data.get('reason', 'Unknown'),
                'quality_score': event.data.get('quality_score', 0)
            })

        elif event.event_type == EventType.PROCESSING_COMPLETED:
            quality_data = event.data.get('quality_metrics', {})

            if 'quality_score' in quality_data:
                self.quality_metrics['quality_scores'].append(quality_data['quality_score'])

            if 'complexity_score' in quality_data:
                self.quality_metrics['complexity_scores'].append(quality_data['complexity_score'])

            if 'maintainability_score' in quality_data:
                self.quality_metrics['maintainability_scores'].append(quality_data['maintainability_score'])

    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality summary."""
        summary = {}

        for metric_name, values in self.quality_metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'latest': values[-1]
                }

        summary['quality_failures'] = {
            'total': len(self.quality_failures),
            'recent': self.quality_failures[-3:]  # Last 3 failures
        }

        return summary

    def get_name(self) -> str:
        return "QualityObserver"

    def is_interested_in(self, event_type: EventType) -> bool:
        return event_type in [
            EventType.QUALITY_CHECK_FAILED,
            EventType.PROCESSING_COMPLETED
        ]


class EventPublisher:
    """Event publisher that notifies observers."""

    def __init__(self):
        """Initialize event publisher."""
        self.observers: List[EventObserver] = []
        self.event_queue = queue.Queue()
        self.processing_thread: Optional[threading.Thread] = None
        self.is_running = False
        self._lock = threading.RLock()

    def subscribe(self, observer: EventObserver) -> None:
        """Subscribe an observer to events.

        Args:
            observer: Observer to subscribe
        """
        with self._lock:
            if observer not in self.observers:
                self.observers.append(observer)
                logger.debug(f"Subscribed observer: {observer.get_name()}")

    def unsubscribe(self, observer: EventObserver) -> None:
        """Unsubscribe an observer from events.

        Args:
            observer: Observer to unsubscribe
        """
        with self._lock:
            if observer in self.observers:
                self.observers.remove(observer)
                logger.debug(f"Unsubscribed observer: {observer.get_name()}")

    def publish(self, event: Event) -> None:
        """Publish an event to all interested observers.

        Args:
            event: Event to publish
        """
        if not self.is_running:
            self.start_processing()

        self.event_queue.put(event)

    def start_processing(self) -> None:
        """Start event processing thread."""
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
            self.processing_thread.start()
            logger.debug("Started event processing thread")

    def stop_processing(self) -> None:
        """Stop event processing thread."""
        if self.is_running:
            self.is_running = False
            self.event_queue.put(None)  # Signal to stop
            if self.processing_thread:
                self.processing_thread.join(timeout=5)
            logger.debug("Stopped event processing thread")

    def _process_events(self) -> None:
        """Process events from queue."""
        while self.is_running:
            try:
                event = self.event_queue.get(timeout=1)
                if event is None:  # Stop signal
                    break

                # Notify interested observers (iterate over a snapshot)
                with self._lock:
                    observers_snapshot = list(self.observers)
                for observer in observers_snapshot:
                    try:
                        if observer.is_interested_in(event.event_type):
                            observer.update(event)
                    except Exception as e:
                        logger.exception(f"Error notifying observer {observer.get_name()}")

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def publish_sync(self, event: Event) -> None:
        """Publish event synchronously (for testing or critical events).

        Args:
            event: Event to publish
        """
        with self._lock:
            observers_snapshot = list(self.observers)
        for observer in observers_snapshot:
            try:
                if observer.is_interested_in(event.event_type):
                    observer.update(event)
            except Exception as e:
                logger.exception(f"Error notifying observer {observer.get_name()}")

    def get_observer_count(self) -> int:
        """Get number of subscribed observers."""
        return len(self.observers)

    def get_observers(self) -> List[str]:
        """Get list of observer names."""
        with self._lock:
            return [observer.get_name() for observer in self.observers]


# Global event publisher instance
event_publisher = EventPublisher()


def publish_event(
    event_type: EventType,
    source: str = "",
    data: Optional[Dict[str, Any]] = None,
    severity: str = "info",
    session_id: Optional[str] = None
) -> None:
    """Convenience function to publish an event.

    Args:
        event_type: Type of event
        source: Source of the event
        data: Event data
        severity: Event severity
        session_id: Optional session identifier
    """
    event = Event(
        event_type=event_type,
        source=source,
        data=data or {},
        severity=severity,
        session_id=session_id
    )
    event_publisher.publish(event)


def subscribe_observer(observer: EventObserver) -> None:
    """Subscribe an observer to the global event publisher.

    Args:
        observer: Observer to subscribe
    """
    event_publisher.subscribe(observer)


def get_default_observers() -> List[EventObserver]:
    """Get default set of observers.

    Returns:
        List of default observer instances
    """
    return [
        LoggingObserver(),
        ProgressObserver(),
        PerformanceObserver(),
        QualityObserver()
    ]


def setup_default_observers() -> None:
    """Setup default observers on the global event publisher."""
    for observer in get_default_observers():
        event_publisher.subscribe(observer)

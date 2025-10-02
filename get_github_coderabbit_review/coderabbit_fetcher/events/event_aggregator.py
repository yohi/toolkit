"""Event aggregator implementation for CodeRabbit fetcher."""

import logging
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from ..patterns.observer import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class EventWindow:
    """Time window for event aggregation."""

    start_time: datetime
    end_time: datetime
    events: List[Event] = field(default_factory=list)

    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within window."""
        return self.start_time <= timestamp <= self.end_time

    def add_event(self, event: Event) -> None:
        """Add event to window."""
        if self.contains(event.timestamp):
            self.events.append(event)

    def get_duration_seconds(self) -> float:
        """Get window duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()


@dataclass
class AggregatedEvent:
    """Aggregated event data."""

    event_type: EventType
    window: EventWindow
    count: int
    sources: Set[str] = field(default_factory=set)
    session_ids: Set[str] = field(default_factory=set)
    severity_counts: Dict[str, int] = field(default_factory=dict)
    data_summary: Dict[str, Any] = field(default_factory=dict)
    first_event: Optional[Event] = None
    last_event: Optional[Event] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "window_start": self.window.start_time.isoformat(),
            "window_end": self.window.end_time.isoformat(),
            "count": self.count,
            "sources": list(self.sources),
            "session_ids": list(self.session_ids),
            "severity_counts": self.severity_counts,
            "data_summary": self.data_summary,
            "first_event_timestamp": (
                self.first_event.timestamp.isoformat() if self.first_event else None
            ),
            "last_event_timestamp": (
                self.last_event.timestamp.isoformat() if self.last_event else None
            ),
        }


class EventAggregator:
    """Event aggregator for collecting and summarizing events."""

    def __init__(
        self,
        window_size_seconds: int = 60,
        max_windows: int = 100,
        aggregation_functions: Optional[Dict[str, Callable]] = None,
    ):
        """Initialize event aggregator.

        Args:
            window_size_seconds: Size of aggregation window in seconds
            max_windows: Maximum number of windows to keep
            aggregation_functions: Custom aggregation functions by event type
        """
        self.window_size_seconds = window_size_seconds
        self.max_windows = max_windows
        self.aggregation_functions = aggregation_functions or {}

        # Storage
        self._windows: deque[EventWindow] = deque(maxlen=max_windows)
        self._current_window: Optional[EventWindow] = None
        self._aggregated_events: Dict[EventType, List[AggregatedEvent]] = defaultdict(list)

        # Thread safety
        self._lock = threading.RLock()

        # Statistics
        self.stats = {
            "events_processed": 0,
            "windows_created": 0,
            "aggregations_created": 0,
            "window_rotations": 0,
        }

    def add_event(self, event: Event) -> None:
        """Add event to aggregator.

        Args:
            event: Event to add
        """
        with self._lock:
            self._ensure_current_window(event.timestamp)

            if self._current_window and self._current_window.contains(event.timestamp):
                self._current_window.add_event(event)
                self.stats["events_processed"] += 1

                logger.debug(f"Added event {event.event_type.value} to current window")
            else:
                logger.warning(f"Event timestamp {event.timestamp} outside current window")

    def aggregate_events(self, force: bool = False) -> Dict[EventType, List[AggregatedEvent]]:
        """Aggregate events in completed windows.

        Args:
            force: Force aggregation of current window

        Returns:
            Dictionary of aggregated events by type
        """
        with self._lock:
            # Force close current window if requested
            if force and self._current_window:
                self._finalize_current_window()

            # Aggregate completed windows
            for window in list(self._windows):
                if window.events:
                    aggregated = self._aggregate_window(window)
                    for event_type, agg_events in aggregated.items():
                        self._aggregated_events[event_type].extend(agg_events)
                        self.stats["aggregations_created"] += len(agg_events)

                    # Clear window events to avoid re-processing
                    window.events.clear()

            return dict(self._aggregated_events)

    def get_aggregated_events(
        self,
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AggregatedEvent]:
        """Get aggregated events with filters.

        Args:
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            List of matching aggregated events
        """
        with self._lock:
            results = []

            event_types_to_check = (
                [event_type] if event_type else list(self._aggregated_events.keys())
            )

            for et in event_types_to_check:
                for agg_event in self._aggregated_events[et]:
                    # Apply time filters
                    if start_time and agg_event.window.end_time < start_time:
                        continue
                    if end_time and agg_event.window.start_time > end_time:
                        continue

                    results.append(agg_event)

            # Sort by window start time
            results.sort(key=lambda ae: ae.window.start_time)

            return results

    def get_event_counts(
        self, event_type: Optional[EventType] = None, time_range_minutes: int = 60
    ) -> Dict[str, int]:
        """Get event counts over time range.

        Args:
            event_type: Filter by event type
            time_range_minutes: Time range in minutes

        Returns:
            Dictionary of event counts
        """
        with self._lock:
            end_time = datetime.now(tz=timezone.utc)
            start_time = end_time - timedelta(minutes=time_range_minutes)

            aggregated = self.get_aggregated_events(event_type, start_time, end_time)

            counts: defaultdict[str, int] = defaultdict(int)

            for agg_event in aggregated:
                key = agg_event.event_type.value
                counts[key] += agg_event.count

            return dict(counts)

    def get_rate_statistics(
        self, event_type: EventType, time_range_minutes: int = 60
    ) -> Dict[str, float]:
        """Get rate statistics for event type.

        Args:
            event_type: Event type to analyze
            time_range_minutes: Time range in minutes

        Returns:
            Rate statistics
        """
        with self._lock:
            end_time = datetime.now(tz=timezone.utc)
            start_time = end_time - timedelta(minutes=time_range_minutes)

            aggregated = self.get_aggregated_events(event_type, start_time, end_time)

            if not aggregated:
                return {
                    "total_events": 0,
                    "events_per_minute": 0.0,
                    "events_per_second": 0.0,
                    "peak_rate_per_minute": 0.0,
                }

            total_events = sum(agg.count for agg in aggregated)
            total_time_minutes = time_range_minutes

            # Calculate rates
            events_per_minute = total_events / total_time_minutes if total_time_minutes > 0 else 0
            events_per_second = events_per_minute / 60

            # Find peak rate (highest count in any window)
            peak_count = max(agg.count for agg in aggregated)
            window_minutes = self.window_size_seconds / 60
            peak_rate_per_minute = peak_count / window_minutes if window_minutes > 0 else 0

            return {
                "total_events": total_events,
                "events_per_minute": events_per_minute,
                "events_per_second": events_per_second,
                "peak_rate_per_minute": peak_rate_per_minute,
                "time_range_minutes": time_range_minutes,
                "window_count": len(aggregated),
            }

    def clear_old_data(self, older_than_minutes: int = 60) -> int:
        """Clear aggregated data older than specified time.

        Args:
            older_than_minutes: Clear data older than this many minutes

        Returns:
            Number of aggregated events cleared
        """
        with self._lock:
            cutoff_time = datetime.now(tz=timezone.utc) - timedelta(minutes=older_than_minutes)
            cleared_count = 0

            for event_type in list(self._aggregated_events.keys()):
                original_count = len(self._aggregated_events[event_type])

                # Keep only recent aggregated events
                self._aggregated_events[event_type] = [
                    agg
                    for agg in self._aggregated_events[event_type]
                    if agg.window.end_time >= cutoff_time
                ]

                cleared_count += original_count - len(self._aggregated_events[event_type])

            logger.info(f"Cleared {cleared_count} old aggregated events")
            return cleared_count

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics.

        Returns:
            Statistics dictionary
        """
        with self._lock:
            stats = self.stats.copy()

            stats.update(
                {
                    "current_windows": len(self._windows),
                    "max_windows": self.max_windows,
                    "window_size_seconds": self.window_size_seconds,
                    "aggregated_event_types": len(self._aggregated_events),
                    "total_aggregated_events": sum(
                        len(events) for events in self._aggregated_events.values()
                    ),
                    "current_window_start": (
                        self._current_window.start_time.isoformat()
                        if self._current_window
                        else None
                    ),
                    "current_window_event_count": (
                        len(self._current_window.events) if self._current_window else 0
                    ),
                }
            )

            return stats

    def _ensure_current_window(self, timestamp: datetime) -> None:
        """Ensure there's a current window for the timestamp."""
        if not self._current_window or not self._current_window.contains(timestamp):
            # Finalize current window if it exists
            if self._current_window:
                self._finalize_current_window()

            # Create new window
            self._create_window_for_timestamp(timestamp)

    def _create_window_for_timestamp(self, timestamp: datetime) -> None:
        """Create a new window containing the timestamp."""
        # Align to window boundaries
        epoch_seconds = timestamp.timestamp()
        window_start_seconds = (
            epoch_seconds // self.window_size_seconds
        ) * self.window_size_seconds

        start_time = datetime.fromtimestamp(window_start_seconds)
        end_time = start_time + timedelta(seconds=self.window_size_seconds)

        self._current_window = EventWindow(start_time=start_time, end_time=end_time)

        self.stats["windows_created"] += 1
        logger.debug(f"Created new window: {start_time} to {end_time}")

    def _finalize_current_window(self) -> None:
        """Finalize current window and add to completed windows."""
        if self._current_window:
            self._windows.append(self._current_window)
            self.stats["window_rotations"] += 1

            logger.debug(
                f"Finalized window with {len(self._current_window.events)} events: "
                f"{self._current_window.start_time} to {self._current_window.end_time}"
            )

            self._current_window = None

    def _aggregate_window(self, window: EventWindow) -> Dict[EventType, List[AggregatedEvent]]:
        """Aggregate events in a window.

        Args:
            window: Window to aggregate

        Returns:
            Dictionary of aggregated events by type
        """
        aggregated = defaultdict(list)

        # Group events by type
        events_by_type = defaultdict(list)
        for event in window.events:
            events_by_type[event.event_type].append(event)

        # Create aggregated event for each type
        for event_type, events in events_by_type.items():
            if not events:
                continue

            # Basic aggregation
            sources = {event.source for event in events}
            session_ids = {event.session_id for event in events if event.session_id}
            severity_counts: defaultdict[str, int] = defaultdict(int)

            for event in events:
                severity_counts[event.severity] += 1

            # Sort events by timestamp
            sorted_events = sorted(events, key=lambda e: e.timestamp)

            # Custom aggregation if available
            data_summary = {}
            if event_type.value in self.aggregation_functions:
                try:
                    data_summary = self.aggregation_functions[event_type.value](events)
                except Exception as e:
                    logger.error(f"Custom aggregation failed for {event_type.value}: {e}")
            else:
                # Default data summary
                data_summary = self._default_data_aggregation(events)

            agg_event = AggregatedEvent(
                event_type=event_type,
                window=window,
                count=len(events),
                sources=sources,
                session_ids=session_ids,
                severity_counts=dict(severity_counts),
                data_summary=data_summary,
                first_event=sorted_events[0],
                last_event=sorted_events[-1],
            )

            aggregated[event_type].append(agg_event)

        return aggregated

    def _default_data_aggregation(self, events: List[Event]) -> Dict[str, Any]:
        """Default data aggregation for events.

        Args:
            events: Events to aggregate

        Returns:
            Aggregated data summary
        """
        if not events:
            return {}

        # Count common data keys
        key_counts: defaultdict[str, int] = defaultdict(int)
        value_samples: defaultdict[str, set[Any]] = defaultdict(set)

        for event in events:
            for key, value in event.data.items():
                key_counts[key] += 1
                # Keep a sample of values (limited to avoid memory issues)
                if len(value_samples[key]) < 10:
                    value_samples[key].add(str(value))

        return {
            "common_data_keys": dict(key_counts),
            "value_samples": {k: list(v) for k, v in value_samples.items()},
            "total_events": len(events),
        }


def create_progress_aggregation_function() -> Callable[[List[Event]], Dict[str, Any]]:
    """Create aggregation function for progress events."""

    def aggregate_progress(events: List[Event]) -> Dict[str, Any]:
        if not events:
            return {}

        phases = set()
        progress_values = []
        sessions = set()

        for event in events:
            data = event.data
            if "phase" in data:
                phases.add(data["phase"])
            if "progress_percent" in data:
                try:
                    progress_values.append(float(data["progress_percent"]))
                except (ValueError, TypeError):
                    pass
            if event.session_id:
                sessions.add(event.session_id)

        summary = {
            "unique_phases": list(phases),
            "unique_sessions": list(sessions),
            "phase_count": len(phases),
            "session_count": len(sessions),
        }

        if progress_values:
            summary.update(
                {
                    "min_progress": min(progress_values),
                    "max_progress": max(progress_values),
                    "avg_progress": sum(progress_values) / len(progress_values),
                }
            )

        return summary

    return aggregate_progress


def create_error_aggregation_function() -> Callable[[List[Event]], Dict[str, Any]]:
    """Create aggregation function for error events."""

    def aggregate_errors(events: List[Event]) -> Dict[str, Any]:
        if not events:
            return {}

        error_types: defaultdict[str, int] = defaultdict(int)
        error_messages = set()
        sources = set()

        for event in events:
            data = event.data
            if "error_type" in data:
                error_types[data["error_type"]] += 1
            if "error" in data:
                # Keep first 100 chars of error message
                error_msg = str(data["error"])[:100]
                error_messages.add(error_msg)
            sources.add(event.source)

        return {
            "error_types": dict(error_types),
            "sample_error_messages": list(error_messages),
            "error_sources": list(sources),
            "unique_error_types": len(error_types),
            "unique_sources": len(sources),
        }

    return aggregate_errors

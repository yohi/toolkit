"""Event system module for CodeRabbit fetcher."""

from ..patterns.observer import (
    Event,
    EventObserver,
    EventPublisher,
    EventType,
    LoggingObserver,
    PerformanceObserver,
    ProgressObserver,
    QualityObserver,
    publish_event,
    setup_default_observers,
    subscribe_observer,
)
from .event_aggregator import AggregatedEvent, EventAggregator, EventWindow
from .event_bus import (
    AsyncEventHandler,
    EventBus,
    EventHandler,
    EventMiddleware,
    async_event_handler,
    event_handler,
)
from .event_store import EventRecord, EventStore, FileEventStore, InMemoryEventStore

__all__ = [
    # Observer Pattern (from patterns module)
    "EventType",
    "Event",
    "EventObserver",
    "EventPublisher",
    "LoggingObserver",
    "ProgressObserver",
    "PerformanceObserver",
    "QualityObserver",
    "publish_event",
    "subscribe_observer",
    "setup_default_observers",
    # Event Bus
    "EventBus",
    "EventHandler",
    "AsyncEventHandler",
    "EventMiddleware",
    "event_handler",
    "async_event_handler",
    # Event Store
    "EventStore",
    "EventRecord",
    "InMemoryEventStore",
    "FileEventStore",
    # Event Aggregator
    "EventAggregator",
    "AggregatedEvent",
    "EventWindow",
]

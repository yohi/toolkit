"""Event system module for CodeRabbit fetcher."""

from ..patterns.observer import (
    EventType,
    Event,
    EventObserver,
    EventPublisher,
    LoggingObserver,
    ProgressObserver,
    PerformanceObserver,
    QualityObserver,
    publish_event,
    subscribe_observer,
    setup_default_observers
)

from .event_bus import (
    EventBus,
    EventHandler,
    AsyncEventHandler,
    EventMiddleware,
    event_handler,
    async_event_handler
)

from .event_store import (
    EventStore,
    EventRecord,
    InMemoryEventStore,
    FileEventStore
)

from .event_aggregator import (
    EventAggregator,
    AggregatedEvent,
    EventWindow
)

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
    "EventWindow"
]

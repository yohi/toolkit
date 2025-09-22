"""Design patterns module for CodeRabbit fetcher."""

from .factory import (
    AnalyzerFactory,
    ComponentCreationError,
    ComponentFactory,
    ComponentFactoryManager,
    FormatterFactory,
    ProcessorFactory,
    UtilityFactory,
    create_component,
    get_supported_components,
)
from .observer import (
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
from .strategy import (
    ProcessingContext,
    ProcessingMode,
    ProcessingStrategy,
    ProcessingStrategyManager,
    get_available_strategies,
    process_with_strategy,
)

__all__ = [
    # Factory Pattern
    "ComponentFactory",
    "ProcessorFactory",
    "FormatterFactory",
    "AnalyzerFactory",
    "UtilityFactory",
    "ComponentFactoryManager",
    "ComponentCreationError",
    "create_component",
    "get_supported_components",
    # Strategy Pattern
    "ProcessingStrategy",
    "ProcessingMode",
    "ProcessingContext",
    "ProcessingStrategyManager",
    "process_with_strategy",
    "get_available_strategies",
    # Observer Pattern
    "EventObserver",
    "EventType",
    "Event",
    "EventPublisher",
    "LoggingObserver",
    "ProgressObserver",
    "PerformanceObserver",
    "QualityObserver",
    "publish_event",
    "subscribe_observer",
    "setup_default_observers",
]

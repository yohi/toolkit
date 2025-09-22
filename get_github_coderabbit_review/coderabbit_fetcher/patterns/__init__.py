"""Design patterns module for CodeRabbit fetcher."""

from .factory import (
    ComponentFactory,
    ProcessorFactory,
    FormatterFactory,
    AnalyzerFactory,
    UtilityFactory,
    ComponentFactoryManager,
    ComponentCreationError,
    create_component,
    get_supported_components
)

from .strategy import (
    ProcessingStrategy,
    ProcessingMode,
    ProcessingContext,
    ProcessingStrategyManager,
    process_with_strategy,
    get_available_strategies
)

from .observer import (
    EventObserver,
    EventType,
    Event,
    EventPublisher,
    LoggingObserver,
    ProgressObserver,
    PerformanceObserver,
    QualityObserver,
    publish_event,
    subscribe_observer,
    setup_default_observers
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
    "setup_default_observers"
]

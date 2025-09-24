"""Factory pattern implementations for CodeRabbit fetcher components."""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Enumeration of component types."""

    PROCESSOR = "processor"
    FORMATTER = "formatter"
    ANALYZER = "analyzer"
    UTILITY = "utility"


class ComponentCreationError(Exception):
    """Exception raised when component creation fails."""

    pass


class ComponentFactory(ABC):
    """Abstract base class for component factories."""

    @abstractmethod
    def create(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """Create a component of the specified type.

        Args:
            component_type: Type of component to create
            config: Optional configuration for the component

        Returns:
            Created component instance

        Raises:
            ComponentCreationError: If component creation fails
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Get list of supported component types.

        Returns:
            List of supported component type names
        """
        pass


class ProcessorFactory(ComponentFactory):
    """Factory for creating processor components."""

    def __init__(self) -> None:
        """Initialize processor factory."""
        self._processor_registry: Dict[str, Type] = {}
        self._register_default_processors()

    def _register_default_processors(self) -> None:
        """Register default processor types."""
        try:
            from ..processors import ReviewProcessor, SummaryProcessor, ThreadProcessor

            self._processor_registry.update(
                {
                    "review": ReviewProcessor,
                    "summary": SummaryProcessor,
                    "thread": ThreadProcessor,
                }
            )
        except ImportError as e:
            logger.warning(f"Could not import some processors: {e}")

    def create(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """Create a processor component."""
        config = config or {}

        if component_type not in self._processor_registry:
            raise ComponentCreationError(
                f"Unsupported processor type: {component_type}. "
                f"Supported types: {list(self._processor_registry.keys())}"
            )

        processor_class = self._processor_registry[component_type]

        try:
            if component_type == "thread":
                resolved_marker = config.get("resolved_marker", "🔒 CODERABBIT_RESOLVED 🔒")
                return processor_class(resolved_marker)
            else:
                return processor_class()

        except Exception as e:
            raise ComponentCreationError(f"Failed to create {component_type} processor: {e}") from e

    def get_supported_types(self) -> List[str]:
        """Get supported processor types."""
        return list(self._processor_registry.keys())

    def register_processor(self, name: str, processor_class: Type) -> None:
        """Register a new processor type."""
        self._processor_registry[name] = processor_class
        logger.debug(f"Registered processor: {name}")


class FormatterFactory(ComponentFactory):
    """Factory for creating formatter components."""

    def __init__(self) -> None:
        """Initialize formatter factory."""
        self._formatter_registry: Dict[str, Type] = {}
        self._register_default_formatters()

    def _register_default_formatters(self):
        """Register default formatter types."""
        try:
            from ..formatters import (
                AIAgentPromptFormatter,
                JSONFormatter,
                LLMInstructionFormatter,
                MarkdownFormatter,
                PlainTextFormatter,
            )

            self._formatter_registry.update(
                {
                    "markdown": MarkdownFormatter,
                    "json": JSONFormatter,
                    "plain": PlainTextFormatter,
                    "llm-instruction": LLMInstructionFormatter,
                    "ai-agent-prompt": AIAgentPromptFormatter,
                }
            )
        except ImportError as e:
            logger.warning(f"Could not import some formatters: {e}")

    def create(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """Create a formatter component."""
        config = config or {}

        if component_type not in self._formatter_registry:
            raise ComponentCreationError(
                f"Unsupported formatter type: {component_type}. "
                f"Supported types: {list(self._formatter_registry.keys())}"
            )

        formatter_class = self._formatter_registry[component_type]

        try:
            if component_type == "markdown":
                return formatter_class(
                    include_metadata=config.get("include_metadata", True),
                    include_toc=config.get("include_toc", True),
                )
            else:
                return formatter_class()

        except Exception as e:
            raise ComponentCreationError(f"Failed to create {component_type} formatter: {e}") from e

    def get_supported_types(self) -> List[str]:
        """Get supported formatter types."""
        return list(self._formatter_registry.keys())

    def register_formatter(self, name: str, formatter_class: Type) -> None:
        """Register a new formatter type."""
        self._formatter_registry[name] = formatter_class
        logger.debug(f"Registered formatter: {name}")


class AnalyzerFactory(ComponentFactory):
    """Factory for creating analyzer components."""

    def __init__(self):
        """Initialize analyzer factory."""
        self._analyzer_registry: Dict[str, Type] = {}
        self._register_default_analyzers()

    def _register_default_analyzers(self):
        """Register default analyzer types."""
        try:
            from ..analyzers import CommentClassifier, MetadataEnhancer, ResolutionDetector

            self._analyzer_registry.update(
                {
                    "classifier": CommentClassifier,
                    "metadata_enhancer": MetadataEnhancer,
                    "resolution_detector": ResolutionDetector,
                }
            )
        except ImportError as e:
            logger.warning(f"Could not import some analyzers: {e}")

    def create(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """Create an analyzer component."""
        config = config or {}

        if component_type not in self._analyzer_registry:
            raise ComponentCreationError(
                f"Unsupported analyzer type: {component_type}. "
                f"Supported types: {list(self._analyzer_registry.keys())}"
            )

        analyzer_class = self._analyzer_registry[component_type]

        try:
            if component_type == "classifier":
                return analyzer_class(config=config)
            else:
                return analyzer_class()

        except Exception as e:
            raise ComponentCreationError(f"Failed to create {component_type} analyzer: {e}") from e

    def get_supported_types(self) -> List[str]:
        """Get supported analyzer types."""
        return list(self._analyzer_registry.keys())

    def register_analyzer(self, name: str, analyzer_class: Type) -> None:
        """Register a new analyzer type."""
        self._analyzer_registry[name] = analyzer_class
        logger.debug(f"Registered analyzer: {name}")


class UtilityFactory(ComponentFactory):
    """Factory for creating utility components."""

    def __init__(self):
        """Initialize utility factory."""
        self._utility_registry: Dict[str, Type] = {}
        self._register_default_utilities()

    def _register_default_utilities(self):
        """Register default utility types."""
        try:
            from ..utils.code_quality import QualityGate
            from ..utils.memory_manager import MemoryManager
            from ..utils.streaming_processor import CommentStreamProcessor

            self._utility_registry.update(
                {
                    "memory_manager": MemoryManager,
                    "stream_processor": CommentStreamProcessor,
                    "quality_gate": QualityGate,
                }
            )
        except ImportError as e:
            logger.warning(f"Could not import some utilities: {e}")

    def create(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """Create a utility component."""
        config = config or {}

        if component_type not in self._utility_registry:
            raise ComponentCreationError(
                f"Unsupported utility type: {component_type}. "
                f"Supported types: {list(self._utility_registry.keys())}"
            )

        utility_class = self._utility_registry[component_type]

        try:
            if component_type == "memory_manager":
                max_memory_mb = config.get("max_memory_mb", 300)
                return utility_class(max_memory_mb=max_memory_mb)
            elif component_type == "stream_processor":
                max_workers = config.get("max_workers", 3)
                batch_size = config.get("batch_size", 25)
                return utility_class(max_workers=max_workers, batch_size=batch_size)
            elif component_type == "quality_gate":
                max_complexity = config.get("max_complexity", 10)
                max_lines = config.get("max_lines", 50)
                return utility_class(max_complexity=max_complexity, max_lines=max_lines)
            else:
                return utility_class()

        except Exception as e:
            raise ComponentCreationError(f"Failed to create {component_type} utility: {e}") from e

    def get_supported_types(self) -> List[str]:
        """Get supported utility types."""
        return list(self._utility_registry.keys())

    def register_utility(self, name: str, utility_class: Type) -> None:
        """Register a new utility type."""
        self._utility_registry[name] = utility_class
        logger.debug(f"Registered utility: {name}")


class ComponentFactoryManager:
    """Central manager for all component factories."""

    def __init__(self):
        """Initialize the factory manager."""
        self._factories: Dict[ComponentType, ComponentFactory] = {
            ComponentType.PROCESSOR: ProcessorFactory(),
            ComponentType.FORMATTER: FormatterFactory(),
            ComponentType.ANALYZER: AnalyzerFactory(),
            ComponentType.UTILITY: UtilityFactory(),
        }

    def create_component(
        self,
        component_category: Union[ComponentType, str],
        component_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Create a component using the appropriate factory."""
        # Convert string to ComponentType if needed
        if isinstance(component_category, str):
            try:
                component_category = ComponentType(component_category)
            except ValueError:
                raise ComponentCreationError(f"Invalid component category: {component_category}")

        if component_category not in self._factories:
            raise ComponentCreationError(f"No factory available for category: {component_category}")

        factory = self._factories[component_category]

        try:
            return factory.create(component_type, config)
        except Exception as e:
            logger.error(f"Failed to create component {component_category}.{component_type}: {e}")
            raise

    def get_supported_components(self) -> Dict[str, List[str]]:
        """Get all supported component types by category."""
        result = {}
        for category, factory in self._factories.items():
            result[category.value] = factory.get_supported_types()
        return result

    def register_factory(
        self, component_category: ComponentType, factory: ComponentFactory
    ) -> None:
        """Register a new factory for a component category."""
        self._factories[component_category] = factory
        logger.info(f"Registered factory for category: {component_category}")


# Global factory manager instance
factory_manager = ComponentFactoryManager()


def create_component(
    component_category: Union[ComponentType, str],
    component_type: str,
    config: Optional[Dict[str, Any]] = None,
) -> Any:
    """Convenience function to create components using the global factory manager."""
    return factory_manager.create_component(component_category, component_type, config)


def get_supported_components() -> Dict[str, List[str]]:
    """Get all supported component types."""
    return factory_manager.get_supported_components()

"""Strategy pattern implementations for CodeRabbit fetcher."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Processing mode enumeration."""

    FAST = "fast"
    BALANCED = "balanced"
    THOROUGH = "thorough"
    MEMORY_EFFICIENT = "memory_efficient"


@dataclass
class ProcessingContext:
    """Context for processing strategies."""

    mode: ProcessingMode
    max_memory_mb: int = 300
    max_workers: int = 3
    batch_size: int = 25
    quality_threshold: float = 0.8
    timeout_seconds: int = 300
    parallel_enabled: bool = True
    cache_enabled: bool = True


class ProcessingStrategy(ABC):
    """Abstract base class for processing strategies."""

    @abstractmethod
    def process(self, data: Any, context: ProcessingContext) -> Any:
        """Process data using this strategy.

        Args:
            data: Data to process
            context: Processing context with configuration

        Returns:
            Processed result
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get strategy description."""
        pass

    def is_suitable_for(self, data_size: int, available_memory: int) -> bool:
        """Check if strategy is suitable for given constraints.

        Args:
            data_size: Size of data to process
            available_memory: Available memory in MB

        Returns:
            True if strategy is suitable
        """
        return True  # Default implementation


class FastProcessingStrategy(ProcessingStrategy):
    """Fast processing strategy optimized for speed."""

    def process(self, data: Any, context: ProcessingContext) -> Any:
        """Process data with fast strategy."""
        logger.info("Using fast processing strategy")

        # Optimize for speed - use replace to avoid modifying original context
        optimized_context = replace(
            context,
            batch_size=min(context.batch_size * 2, 100),
            max_workers=min(context.max_workers * 2, 8),
            quality_threshold=0.6,  # Lower quality threshold for speed
        )

        return self._process_with_optimizations(data, optimized_context)

    def _process_with_optimizations(self, data: Any, optimized_context: ProcessingContext) -> Any:
        """Process with speed optimizations."""
        from ..utils.streaming_processor import CommentStreamProcessor

        processor = CommentStreamProcessor(
            max_workers=optimized_context.max_workers, batch_size=optimized_context.batch_size
        )

        def fast_processor(item):
            # Minimal processing for speed
            return self._minimal_processing(item)

        if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
            return processor.process_streaming(
                list(data), fast_processor, parallel=optimized_context.parallel_enabled
            )
        else:
            return fast_processor(data)

    def _minimal_processing(self, item: Any) -> Any:
        """Minimal processing for maximum speed."""
        # Basic processing only
        if isinstance(item, dict):
            return {"id": item.get("id"), "processed": True, "strategy": "fast"}
        return {"item": item, "processed": True, "strategy": "fast"}

    def get_name(self) -> str:
        return "Fast Processing"

    def get_description(self) -> str:
        return "Optimized for maximum speed with minimal quality checks"

    def is_suitable_for(self, data_size: int, available_memory: int) -> bool:
        return data_size < 500 and available_memory > 100


class BalancedProcessingStrategy(ProcessingStrategy):
    """Balanced processing strategy for optimal speed/quality trade-off."""

    def process(self, data: Any, context: ProcessingContext) -> Any:
        """Process data with balanced strategy."""
        logger.info("Using balanced processing strategy")

        # Keep default settings for balance
        return self._process_with_balance(data, context)

    def _process_with_balance(self, data: Any, context: ProcessingContext) -> Any:
        """Process with balanced approach."""
        from ..utils.memory_manager import MemoryManager

        # Use memory manager for efficiency
        memory_manager = MemoryManager(max_memory_mb=context.max_memory_mb)

        def balanced_processor(item):
            return self._balanced_processing(item, context)

        if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
            return memory_manager.process_with_memory_limit(
                list(data), balanced_processor, batch_size=context.batch_size
            )
        else:
            return balanced_processor(data)

    def _balanced_processing(self, item: Any, context: ProcessingContext) -> Any:
        """Balanced processing with moderate quality checks."""
        if isinstance(item, dict):
            # Moderate processing
            result = {
                "id": item.get("id"),
                "content": item.get("body", item.get("content", "")),
                "processed": True,
                "strategy": "balanced",
            }

            # Add quality score if applicable
            content = result.get("content", "")
            if content:
                result["quality_score"] = min(len(content) / 100.0, 1.0)

            return result

        return {"item": item, "processed": True, "strategy": "balanced"}

    def get_name(self) -> str:
        return "Balanced Processing"

    def get_description(self) -> str:
        return "Optimal balance between processing speed and quality"

    def is_suitable_for(self, data_size: int, available_memory: int) -> bool:
        return True  # Suitable for most cases


class ThoroughProcessingStrategy(ProcessingStrategy):
    """Thorough processing strategy optimized for quality."""

    def process(self, data: Any, context: ProcessingContext) -> Any:
        """Process data with thorough strategy."""
        logger.info("Using thorough processing strategy")

        # Optimize for quality
        context.quality_threshold = 0.95
        context.batch_size = min(context.batch_size, 10)  # Smaller batches for quality

        return self._process_with_quality_focus(data, context)

    def _process_with_quality_focus(self, data: Any, context: ProcessingContext) -> Any:
        """Process with quality focus."""
        from ..utils.code_quality import CodeQualityAnalyzer, QualityGate

        quality_gate = QualityGate(max_complexity=8, max_lines=40)
        analyzer = CodeQualityAnalyzer()

        def thorough_processor(item):
            return self._thorough_processing(item, quality_gate, analyzer, context)

        if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
            results = []
            for item in data:
                result = thorough_processor(item)
                if result:
                    results.append(result)
            return results
        else:
            return thorough_processor(data)

    def _thorough_processing(
        self, item: Any, quality_gate, analyzer, context: ProcessingContext
    ) -> Any:
        """Thorough processing with comprehensive quality checks."""
        if isinstance(item, dict):
            content = item.get("body", item.get("content", ""))

            result = {
                "id": item.get("id"),
                "content": content,
                "processed": True,
                "strategy": "thorough",
            }

            # Comprehensive quality analysis
            if content:
                quality_check = quality_gate.check_quality(content)
                complexity_score = analyzer.calculate_complexity_score(content)
                suggestions = analyzer.suggest_refactoring(content)

                result.update(
                    {
                        "quality_gate_passed": quality_check["passes_quality_gate"],
                        "quality_score": quality_check["quality_score"] / 100.0,
                        "complexity_metrics": complexity_score,
                        "improvement_suggestions": suggestions,
                        "meets_threshold": quality_check["quality_score"]
                        >= context.quality_threshold * 100,
                    }
                )

            return result

        return {"item": item, "processed": True, "strategy": "thorough"}

    def get_name(self) -> str:
        return "Thorough Processing"

    def get_description(self) -> str:
        return "Comprehensive processing with extensive quality analysis"

    def is_suitable_for(self, data_size: int, available_memory: int) -> bool:
        return data_size < 200 and available_memory > 200


class MemoryEfficientStrategy(ProcessingStrategy):
    """Memory-efficient processing strategy for large datasets."""

    def process(self, data: Any, context: ProcessingContext) -> Any:
        """Process data with memory-efficient strategy."""
        logger.info("Using memory-efficient processing strategy")

        # Optimize for memory usage
        context.batch_size = min(context.batch_size, 5)
        context.max_memory_mb = min(context.max_memory_mb, 150)

        return self._process_with_memory_efficiency(data, context)

    def _process_with_memory_efficiency(self, data: Any, context: ProcessingContext) -> Any:
        """Process with memory efficiency focus."""
        from ..utils.memory_manager import MemoryManager, memory_efficient_processing

        memory_manager = MemoryManager(max_memory_mb=context.max_memory_mb)

        @memory_efficient_processing
        def memory_efficient_processor(item):
            return self._memory_efficient_processing(item, memory_manager)

        if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
            # Process in very small batches
            results = []
            for batch in memory_manager.stream_large_list(list(data), context.batch_size):
                batch_results = []
                for item in batch:
                    result = memory_efficient_processor(item)
                    if result:
                        batch_results.append(result)

                results.extend(batch_results)

                # Force memory optimization after each batch
                memory_manager.optimize_memory(force=True)

            return results
        else:
            return memory_efficient_processor(data)

    def _memory_efficient_processing(self, item: Any, memory_manager) -> Any:
        """Memory-efficient processing with minimal memory footprint."""
        if isinstance(item, dict):
            # Minimal data retention
            result = {"id": item.get("id"), "processed": True, "strategy": "memory_efficient"}

            # Only keep essential data
            if "body" in item or "content" in item:
                content = item.get("body", item.get("content", ""))
                # Store only content length, not full content
                result["content_length"] = len(content)
                result["has_content"] = bool(content.strip() if content else False)

            return result

        return {"processed": True, "strategy": "memory_efficient"}

    def get_name(self) -> str:
        return "Memory Efficient"

    def get_description(self) -> str:
        return "Optimized for minimal memory usage with large datasets"

    def is_suitable_for(self, data_size: int, available_memory: int) -> bool:
        return data_size > 1000 or available_memory < 200


class ProcessingStrategyManager:
    """Manager for processing strategies with automatic selection."""

    def __init__(self):
        """Initialize strategy manager."""
        self._strategies: Dict[ProcessingMode, ProcessingStrategy] = {
            ProcessingMode.FAST: FastProcessingStrategy(),
            ProcessingMode.BALANCED: BalancedProcessingStrategy(),
            ProcessingMode.THOROUGH: ThoroughProcessingStrategy(),
            ProcessingMode.MEMORY_EFFICIENT: MemoryEfficientStrategy(),
        }

    def get_strategy(self, mode: ProcessingMode) -> ProcessingStrategy:
        """Get strategy by mode.

        Args:
            mode: Processing mode

        Returns:
            Processing strategy instance

        Raises:
            ValueError: If mode is not supported
        """
        if mode not in self._strategies:
            raise ValueError(f"Unsupported processing mode: {mode}")

        return self._strategies[mode]

    def auto_select_strategy(
        self, data_size: int, available_memory: int, priority: str = "balanced"
    ) -> ProcessingStrategy:
        """Automatically select the best strategy.

        Args:
            data_size: Size of data to process
            available_memory: Available memory in MB
            priority: Priority preference ("speed", "quality", "balanced")

        Returns:
            Best suited processing strategy
        """
        # Check memory constraints first
        if available_memory < 150 or data_size > 1000:
            return self._strategies[ProcessingMode.MEMORY_EFFICIENT]

        # Select based on priority and constraints
        if priority == "speed" and data_size < 500:
            return self._strategies[ProcessingMode.FAST]
        elif priority == "quality" and data_size < 200 and available_memory > 200:
            return self._strategies[ProcessingMode.THOROUGH]
        else:
            return self._strategies[ProcessingMode.BALANCED]

    def process_with_auto_strategy(
        self, data: Any, context: Optional[ProcessingContext] = None, priority: str = "balanced"
    ) -> Any:
        """Process data with automatically selected strategy.

        Args:
            data: Data to process
            context: Optional processing context
            priority: Priority preference

        Returns:
            Processed result
        """
        if context is None:
            context = ProcessingContext(mode=ProcessingMode.BALANCED)

        # Estimate data size
        data_size = self._estimate_data_size(data)

        # Get available memory (simplified estimation)
        try:
            from ..utils.memory_manager import MemoryManager

            memory_manager = MemoryManager()
            memory_stats = memory_manager.get_memory_stats()
            available_memory = memory_stats.available_mb
        except Exception:
            available_memory = 300  # Default assumption

        # Select strategy
        strategy = self.auto_select_strategy(data_size, available_memory, priority)

        logger.info(
            f"Auto-selected strategy: {strategy.get_name()} "
            f"(data_size: {data_size}, available_memory: {available_memory:.1f}MB)"
        )

        return strategy.process(data, context)

    def _estimate_data_size(self, data: Any) -> int:
        """Estimate data size for strategy selection."""
        if hasattr(data, "__len__"):
            return len(data)
        elif hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
            try:
                # 最大1000要素までカウント
                count = 0
                for _ in data:
                    count += 1
                    if count >= 1000:
                        break
                return count
            except Exception:
                return 100  # Default estimate
        else:
            return 1

    def register_strategy(self, mode: ProcessingMode, strategy: ProcessingStrategy) -> None:
        """Register a new processing strategy.

        Args:
            mode: Processing mode for the strategy
            strategy: Strategy instance to register
        """
        self._strategies[mode] = strategy
        logger.info(f"Registered strategy: {mode.value}")

    def get_available_strategies(self) -> Dict[str, str]:
        """Get available strategies with descriptions.

        Returns:
            Dictionary mapping strategy names to descriptions
        """
        return {
            strategy.get_name(): strategy.get_description()
            for strategy in self._strategies.values()
        }


# Global strategy manager instance
strategy_manager = ProcessingStrategyManager()


def process_with_strategy(
    data: Any,
    mode: Union[ProcessingMode, str] = ProcessingMode.BALANCED,
    context: Optional[ProcessingContext] = None,
) -> Any:
    """Convenience function to process data with specified strategy.

    Args:
        data: Data to process
        mode: Processing mode or "auto" for automatic selection
        context: Optional processing context

    Returns:
        Processed result
    """
    if context is None:
        context = ProcessingContext(
            mode=mode if isinstance(mode, ProcessingMode) else ProcessingMode.BALANCED
        )

    if mode == "auto":
        return strategy_manager.process_with_auto_strategy(data, context)

    if isinstance(mode, str):
        mode = ProcessingMode(mode)

    strategy = strategy_manager.get_strategy(mode)
    return strategy.process(data, context)


def get_available_strategies() -> Dict[str, str]:
    """Get available processing strategies.

    Returns:
        Dictionary mapping strategy names to descriptions
    """
    return strategy_manager.get_available_strategies()

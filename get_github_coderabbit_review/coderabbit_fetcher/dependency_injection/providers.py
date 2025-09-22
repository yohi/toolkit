"""Service provider implementations for dependency injection."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Type, Callable, Optional, Dict, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AbstractProvider(ABC):
    """Abstract base class for service providers."""

    @abstractmethod
    def provide(self) -> Any:
        """Provide service instance.

        Returns:
            Service instance
        """
        pass

    @abstractmethod
    def can_provide(self, service_type: Type) -> bool:
        """Check if provider can provide the service type.

        Args:
            service_type: Service type to check

        Returns:
            True if provider can provide the service
        """
        pass


class ClassProvider(AbstractProvider):
    """Provider that creates instances from a class."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .container import DIContainer

    def __init__(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        container: Optional['DIContainer'] = None
    ):
        """Initialize class provider.

        Args:
            service_type: Interface/service type
            implementation_type: Implementation class
            container: DI container for dependency resolution
        """
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.container = container

    def provide(self) -> T:
        """Provide instance by creating from class."""
        if self.container:
            return self.container._create_instance(self.implementation_type)
        else:
            # Fallback to simple instantiation
            return self.implementation_type()

    def can_provide(self, service_type: Type) -> bool:
        """Check if can provide service type."""
        return service_type == self.service_type

    def __repr__(self) -> str:
        return f"ClassProvider({self.service_type.__name__} -> {self.implementation_type.__name__})"


class FactoryProvider(AbstractProvider):
    """Provider that uses a factory function."""

    def __init__(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        container: Optional['DIContainer'] = None
    ):
        """Initialize factory provider.

        Args:
            service_type: Service type to provide
            factory: Factory function
            container: DI container for dependency resolution
        """
        self.service_type = service_type
        self.factory = factory
        self.container = container

    def provide(self) -> T:
        """Provide instance using factory."""
        if self.container:
            return self.container._invoke_factory(self.factory)
        else:
            # Fallback to simple factory call
            return self.factory()

    def can_provide(self, service_type: Type) -> bool:
        """Check if can provide service type."""
        return service_type == self.service_type

    def __repr__(self) -> str:
        return f"FactoryProvider({self.service_type.__name__} -> {self.factory.__name__})"


class InstanceProvider(AbstractProvider):
    """Provider that returns a specific instance."""

    def __init__(self, service_type: Type[T], instance: T):
        """Initialize instance provider.

        Args:
            service_type: Service type
            instance: Service instance
        """
        self.service_type = service_type
        self.instance = instance

    def provide(self) -> T:
        """Provide the specific instance."""
        return self.instance

    def can_provide(self, service_type: Type) -> bool:
        """Check if can provide service type."""
        return service_type == self.service_type

    def __repr__(self) -> str:
        return f"InstanceProvider({self.service_type.__name__})"


class ValueProvider(AbstractProvider):
    """Provider that returns a constant value."""

    def __init__(self, value: Any):
        """Initialize value provider.

        Args:
            value: Value to provide
        """
        self.value = value

    def provide(self) -> Any:
        """Provide the constant value."""
        return self.value

    def can_provide(self, service_type: Type) -> bool:
        """Check if can provide service type."""
        return isinstance(self.value, service_type)

    def __repr__(self) -> str:
        return f"ValueProvider({type(self.value).__name__})"


class DelegateProvider(AbstractProvider):
    """Provider that delegates to another provider."""

    def __init__(
        self,
        service_type: Type[T],
        delegate: Callable[[], T]
    ):
        """Initialize delegate provider.

        Args:
            service_type: Service type
            delegate: Delegate function
        """
        self.service_type = service_type
        self.delegate = delegate

    def provide(self) -> T:
        """Provide instance using delegate."""
        return self.delegate()

    def can_provide(self, service_type: Type) -> bool:
        """Check if can provide service type."""
        return service_type == self.service_type

    def __repr__(self) -> str:
        return f"DelegateProvider({self.service_type.__name__})"


class ConditionalProvider(AbstractProvider):
    """Provider that provides based on conditions."""

    def __init__(
        self,
        service_type: Type[T],
        providers: Dict[Callable[[], bool], AbstractProvider],
        default_provider: Optional[AbstractProvider] = None
    ):
        """Initialize conditional provider.

        Args:
            service_type: Service type
            providers: Condition to provider mappings
            default_provider: Default provider if no conditions match
        """
        self.service_type = service_type
        self.providers = providers
        self.default_provider = default_provider

    def provide(self) -> T:
        """Provide instance based on conditions."""
        # Check conditions in order
        for condition, provider in self.providers.items():
            try:
                if condition():
                    return provider.provide()
            except Exception as e:
                logger.warning(f"Condition check failed: {e}")

        # Use default provider
        if self.default_provider:
            return self.default_provider.provide()

        raise RuntimeError(f"No provider conditions matched for {self.service_type.__name__}")

    def can_provide(self, service_type: Type) -> bool:
        """Check if can provide service type."""
        return service_type == self.service_type

    def __repr__(self) -> str:
        return f"ConditionalProvider({self.service_type.__name__})"


class LazyProvider(AbstractProvider):
    """Provider that lazily creates instances."""

    def __init__(self, service_type: Type[T], provider: AbstractProvider):
        """Initialize lazy provider.

        Args:
            service_type: Service type
            provider: Underlying provider
        """
        self.service_type = service_type
        self.provider = provider
        self._instance: Optional[T] = None
        self._created = False

    def provide(self) -> T:
        """Provide instance lazily."""
        if not self._created:
            self._instance = self.provider.provide()
            self._created = True
            logger.debug(f"Lazily created instance of {self.service_type.__name__}")

        return self._instance

    def can_provide(self, service_type: Type) -> bool:
        """Check if can provide service type."""
        return service_type == self.service_type

    def reset(self) -> None:
        """Reset lazy provider."""
        self._instance = None
        self._created = False

    def __repr__(self) -> str:
        return f"LazyProvider({self.service_type.__name__})"


class PooledProvider(AbstractProvider):
    """Provider that maintains a pool of instances."""

    def __init__(
        self,
        service_type: Type[T],
        provider: AbstractProvider,
        pool_size: int = 10
    ):
        """Initialize pooled provider.

        Args:
            service_type: Service type
            provider: Underlying provider
            pool_size: Maximum pool size
        """
        self.service_type = service_type
        self.provider = provider
        self.pool_size = pool_size
        self._pool: list[T] = []
        self._in_use: set[T] = set()

    def provide(self) -> T:
        """Provide instance from pool."""
        # Try to get from pool
        if self._pool:
            instance = self._pool.pop()
            self._in_use.add(instance)
            logger.debug(f"Provided instance from pool for {self.service_type.__name__}")
            return instance

        # Create new instance if pool is empty
        instance = self.provider.provide()
        self._in_use.add(instance)
        logger.debug(f"Created new pooled instance for {self.service_type.__name__}")
        return instance

    def return_to_pool(self, instance: T) -> None:
        """Return instance to pool.

        Args:
            instance: Instance to return
        """
        if instance in self._in_use:
            self._in_use.remove(instance)

            if len(self._pool) < self.pool_size:
                self._pool.append(instance)
                logger.debug(f"Returned instance to pool for {self.service_type.__name__}")

    def can_provide(self, service_type: Type) -> bool:
        """Check if can provide service type."""
        return service_type == self.service_type

    def get_pool_stats(self) -> Dict[str, int]:
        """Get pool statistics.

        Returns:
            Pool statistics
        """
        return {
            'pool_size': len(self._pool),
            'in_use': len(self._in_use),
            'max_pool_size': self.pool_size
        }

    def __repr__(self) -> str:
        return f"PooledProvider({self.service_type.__name__}, pool_size={self.pool_size})"


class CompositeProvider(AbstractProvider):
    """Provider that composes multiple providers."""

    def __init__(self, providers: list[AbstractProvider]):
        """Initialize composite provider.

        Args:
            providers: List of providers to compose
        """
        self.providers = providers

    def provide(self) -> Any:
        """Provide using first available provider."""
        for provider in self.providers:
            try:
                return provider.provide()
            except Exception as e:
                logger.debug(f"Provider {provider} failed: {e}")
                continue

        raise RuntimeError("No providers could provide the service")

    def can_provide(self, service_type: Type) -> bool:
        """Check if any provider can provide service type."""
        return any(provider.can_provide(service_type) for provider in self.providers)

    def __repr__(self) -> str:
        return f"CompositeProvider({len(self.providers)} providers)"


def create_class_provider(
    service_type: Type[T],
    implementation_type: Type[T],
    container: Optional['DIContainer'] = None
) -> ClassProvider:
    """Create a class provider.

    Args:
        service_type: Service type
        implementation_type: Implementation type
        container: DI container

    Returns:
        Class provider
    """
    return ClassProvider(service_type, implementation_type, container)


def create_factory_provider(
    service_type: Type[T],
    factory: Callable[..., T],
    container: Optional['DIContainer'] = None
) -> FactoryProvider:
    """Create a factory provider.

    Args:
        service_type: Service type
        factory: Factory function
        container: DI container

    Returns:
        Factory provider
    """
    return FactoryProvider(service_type, factory, container)


def create_instance_provider(service_type: Type[T], instance: T) -> InstanceProvider:
    """Create an instance provider.

    Args:
        service_type: Service type
        instance: Service instance

    Returns:
        Instance provider
    """
    return InstanceProvider(service_type, instance)


def create_value_provider(value: Any) -> ValueProvider:
    """Create a value provider.

    Args:
        value: Value to provide

    Returns:
        Value provider
    """
    return ValueProvider(value)

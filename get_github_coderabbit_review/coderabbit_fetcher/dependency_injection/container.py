"""Dependency Injection Container implementation."""

import inspect
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceScope(Enum):
    """Service scope enumeration."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class DIError(Exception):
    """Dependency injection error."""

    pass


class CircularDependencyError(DIError):
    """Circular dependency error."""

    pass


@dataclass
class ServiceBinding:
    """Service binding configuration."""

    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Any = None
    scope: ServiceScope = ServiceScope.TRANSIENT
    metadata: Dict[str, Any] = field(default_factory=dict)


class ServiceProvider(ABC):
    """Abstract service provider."""

    @abstractmethod
    def provide(self, container: "DIContainer", binding: ServiceBinding) -> Any:
        """Provide service instance.

        Args:
            container: DI container
            binding: Service binding

        Returns:
            Service instance
        """
        pass


class SingletonProvider(ServiceProvider):
    """Singleton service provider."""

    def __init__(self) -> None:
        """Initialize singleton provider."""
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()

    def provide(self, container: "DIContainer", binding: ServiceBinding) -> Any:
        """Provide singleton instance."""
        service_type = binding.service_type

        if service_type in self._instances:
            return self._instances[service_type]

        with self._lock:
            # Double-check locking pattern
            if service_type in self._instances:
                return self._instances[service_type]

            # Create new instance
            instance = self._create_instance(container, binding)
            self._instances[service_type] = instance

            logger.debug(f"Created singleton instance for {service_type.__name__}")
            return instance

    def _create_instance(self, container: "DIContainer", binding: ServiceBinding) -> Any:
        """Create service instance."""
        if binding.instance is not None:
            return binding.instance
        elif binding.factory is not None:
            return container._invoke_factory(binding.factory)
        elif binding.implementation_type is not None:
            return container._create_instance(binding.implementation_type)
        else:
            return container._create_instance(binding.service_type)


class TransientProvider(ServiceProvider):
    """Transient service provider."""

    def provide(self, container: "DIContainer", binding: ServiceBinding) -> Any:
        """Provide new instance each time."""
        # Transient scope should always create new instances, ignore binding.instance
        if binding.factory is not None:
            return container._invoke_factory(binding.factory)
        elif binding.implementation_type is not None:
            return container._create_instance(binding.implementation_type)
        else:
            return container._create_instance(binding.service_type)


class ScopedProvider(ServiceProvider):
    """Scoped service provider."""

    def __init__(self):
        """Initialize scoped provider."""
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._lock = threading.RLock()

    def provide(self, container: "DIContainer", binding: ServiceBinding) -> Any:
        """Provide scoped instance."""
        scope_id = container.current_scope_id
        if scope_id is None:
            # Fall back to transient if no scope
            return TransientProvider().provide(container, binding)

        service_type = binding.service_type

        with self._lock:
            if scope_id not in self._scoped_instances:
                self._scoped_instances[scope_id] = {}

            scope_instances = self._scoped_instances[scope_id]

            if service_type in scope_instances:
                return scope_instances[service_type]

            # Create new instance for this scope
            if binding.instance is not None:
                instance = binding.instance
            elif binding.factory is not None:
                instance = container._invoke_factory(binding.factory)
            elif binding.implementation_type is not None:
                instance = container._create_instance(binding.implementation_type)
            else:
                instance = container._create_instance(binding.service_type)

            scope_instances[service_type] = instance
            logger.debug(f"Created scoped instance for {service_type.__name__} in scope {scope_id}")

            return instance

    def clear_scope(self, scope_id: str) -> None:
        """Clear instances for a specific scope."""
        with self._lock:
            if scope_id in self._scoped_instances:
                del self._scoped_instances[scope_id]
                logger.debug(f"Cleared scope {scope_id}")


class DIContainer:
    """Dependency Injection Container."""

    def __init__(self, parent: Optional["DIContainer"] = None):
        """Initialize DI container.

        Args:
            parent: Parent container for hierarchical DI
        """
        self.parent = parent
        self._bindings: Dict[Type, ServiceBinding] = {}
        self._providers: Dict[ServiceScope, ServiceProvider] = {
            ServiceScope.SINGLETON: SingletonProvider(),
            ServiceScope.TRANSIENT: TransientProvider(),
            ServiceScope.SCOPED: ScopedProvider(),
        }
        self._resolution_stack: List[Type] = []
        self._lock = threading.RLock()

        # Scope management
        self.current_scope_id: Optional[str] = None
        self._scope_stack: List[str] = []

        # Container hierarchy
        self._child_containers: List[DIContainer] = []
        if parent:
            parent._child_containers.append(self)

        # Self-register the container
        with self.bind(DIContainer) as b:
            b.to_instance(self)

    def bind(self, service_type: Type[T]) -> "ServiceBinder[T]":
        """Bind a service type.

        Args:
            service_type: Service type to bind

        Returns:
            Service binder for fluent configuration
        """
        return ServiceBinder(self, service_type)

    def get(self, service_type: Type[T]) -> T:
        """Get service instance.

        Args:
            service_type: Service type to resolve

        Returns:
            Service instance

        Raises:
            DIError: If service cannot be resolved
        """
        with self._lock:
            return self._resolve(service_type)

    def try_get(self, service_type: Type[T]) -> Optional[T]:
        """Try to get service instance.

        Args:
            service_type: Service type to resolve

        Returns:
            Service instance or None if not found
        """
        try:
            return self.get(service_type)
        except DIError:
            return None

    def create_scope(self, scope_id: Optional[str] = None) -> "ScopeContext":
        """Create a new scope for scoped services.

        Args:
            scope_id: Optional scope identifier

        Returns:
            Scope context manager
        """
        if scope_id is None:
            import uuid

            scope_id = str(uuid.uuid4())

        return ScopeContext(self, scope_id)

    def create_child_container(self) -> "DIContainer":
        """Create a child container.

        Returns:
            Child container
        """
        return DIContainer(parent=self)

    def _resolve(self, service_type: Type[T]) -> T:
        """Resolve service type."""
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            circular_path = " -> ".join([t.__name__ for t in self._resolution_stack])
            circular_path += f" -> {service_type.__name__}"
            raise CircularDependencyError(f"Circular dependency detected: {circular_path}")

        self._resolution_stack.append(service_type)

        try:
            # Check local bindings first
            if service_type in self._bindings:
                binding = self._bindings[service_type]
                provider = self._providers[binding.scope]
                return provider.provide(self, binding)

            # Check parent container
            if self.parent:
                return self.parent._resolve(service_type)

            # Try to auto-wire if it's a concrete class
            if self._can_auto_wire(service_type):
                logger.debug(f"Auto-wiring {service_type.__name__}")
                return self._create_instance(service_type)

            raise DIError(
                f"Service {service_type.__name__} is not registered and cannot be auto-wired"
            )

        finally:
            self._resolution_stack.pop()

    def _can_auto_wire(self, service_type: Type) -> bool:
        """Check if type can be auto-wired."""
        # Must be a concrete class (not abstract)
        if inspect.isabstract(service_type):
            return False

        # Must have a constructor we can inspect
        try:
            inspect.signature(service_type.__init__)
            return True
        except (ValueError, TypeError):
            return False

    def _create_instance(self, implementation_type: Type) -> Any:
        """Create instance with dependency injection."""
        constructor = implementation_type.__init__
        signature = inspect.signature(constructor)

        # Prepare constructor arguments
        kwargs = {}
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            # Skip parameters with default values if no binding exists
            if param.annotation == param.empty:
                if param.default != param.empty:
                    continue
                else:
                    raise DIError(
                        f"Parameter {param_name} in {implementation_type.__name__} has no type annotation"
                    )

            param_type = param.annotation

            try:
                # Resolve dependency
                dependency = self._resolve(param_type)
                kwargs[param_name] = dependency
            except DIError:
                if param.default != param.empty:
                    # Use default value if available
                    continue
                else:
                    raise

        # Create instance
        try:
            instance = implementation_type(**kwargs)
            logger.debug(f"Created instance of {implementation_type.__name__}")
            return instance
        except Exception as e:
            raise DIError(f"Failed to create instance of {implementation_type.__name__}: {e}")

    def _invoke_factory(self, factory: Callable) -> Any:
        """Invoke factory function with dependency injection."""
        signature = inspect.signature(factory)

        # Prepare factory arguments
        kwargs = {}
        for param_name, param in signature.parameters.items():
            if param.annotation == param.empty:
                if param.default != param.empty:
                    continue
                else:
                    raise DIError(f"Factory parameter {param_name} has no type annotation")

            param_type = param.annotation

            try:
                # Resolve dependency
                dependency = self._resolve(param_type)
                kwargs[param_name] = dependency
            except DIError:
                if param.default != param.empty:
                    # Use default value if available
                    continue
                else:
                    raise

        # Invoke factory
        try:
            return factory(**kwargs)
        except Exception as e:
            raise DIError(f"Factory invocation failed: {e}")

    def _register_binding(self, binding: ServiceBinding) -> None:
        """Register service binding."""
        with self._lock:
            self._bindings[binding.service_type] = binding
            logger.debug(f"Registered binding for {binding.service_type.__name__}")

    def clear_scope(self, scope_id: str) -> None:
        """Clear specific scope."""
        scoped_provider = self._providers[ServiceScope.SCOPED]
        if isinstance(scoped_provider, ScopedProvider):
            scoped_provider.clear_scope(scope_id)

    def get_registered_services(self) -> List[Type]:
        """Get list of registered service types."""
        services = list(self._bindings.keys())
        if self.parent:
            services.extend(self.parent.get_registered_services())
        return list(set(services))  # Remove duplicates


class ServiceBinder(Generic[T]):
    """Fluent service binder."""

    def __init__(self, container: DIContainer, service_type: Type[T]):
        """Initialize service binder.

        Args:
            container: DI container
            service_type: Service type to bind
        """
        self.container = container
        self.service_type = service_type
        self.binding = ServiceBinding(service_type=service_type)

    def to(self, implementation_type: Type[T]) -> "ServiceBinder[T]":
        """Bind to implementation type.

        Args:
            implementation_type: Implementation type

        Returns:
            Self for method chaining
        """
        self.binding.implementation_type = implementation_type
        return self

    def to_factory(self, factory: Callable[..., T]) -> "ServiceBinder[T]":
        """Bind to factory function.

        Args:
            factory: Factory function

        Returns:
            Self for method chaining
        """
        self.binding.factory = factory
        return self

    def to_instance(self, instance: T) -> "ServiceBinder[T]":
        """Bind to specific instance.

        Args:
            instance: Service instance

        Returns:
            Self for method chaining
        """
        self.binding.instance = instance
        self.binding.scope = ServiceScope.SINGLETON
        return self

    def as_singleton(self) -> "ServiceBinder[T]":
        """Configure as singleton.

        Returns:
            Self for method chaining
        """
        self.binding.scope = ServiceScope.SINGLETON
        return self

    def as_transient(self) -> "ServiceBinder[T]":
        """Configure as transient.

        Returns:
            Self for method chaining
        """
        self.binding.scope = ServiceScope.TRANSIENT
        return self

    def as_scoped(self) -> "ServiceBinder[T]":
        """Configure as scoped.

        Returns:
            Self for method chaining
        """
        self.binding.scope = ServiceScope.SCOPED
        return self

    def with_metadata(self, **metadata) -> "ServiceBinder[T]":
        """Add metadata to binding.

        Args:
            **metadata: Metadata key-value pairs

        Returns:
            Self for method chaining
        """
        self.binding.metadata.update(metadata)
        return self

    def __enter__(self) -> "ServiceBinder[T]":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - registers the binding."""
        self.container._register_binding(self.binding)


class ScopeContext:
    """Scope context manager."""

    def __init__(self, container: DIContainer, scope_id: str):
        """Initialize scope context.

        Args:
            container: DI container
            scope_id: Scope identifier
        """
        self.container = container
        self.scope_id = scope_id
        self.previous_scope_id: Optional[str] = None

    def __enter__(self) -> str:
        """Enter scope context."""
        self.previous_scope_id = self.container.current_scope_id
        self.container.current_scope_id = self.scope_id
        self.container._scope_stack.append(self.scope_id)

        logger.debug(f"Entered scope {self.scope_id}")
        return self.scope_id

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit scope context."""
        if self.container._scope_stack:
            self.container._scope_stack.pop()

        self.container.current_scope_id = self.previous_scope_id

        # Clear scope instances
        self.container.clear_scope(self.scope_id)

        logger.debug(f"Exited scope {self.scope_id}")


# Global default container
_default_container = DIContainer()


def get_container() -> DIContainer:
    """Get the default DI container.

    Returns:
        Default DI container
    """
    return _default_container


def set_container(container: DIContainer) -> None:
    """Set the default DI container.

    Args:
        container: DI container to set as default
    """
    global _default_container
    _default_container = container

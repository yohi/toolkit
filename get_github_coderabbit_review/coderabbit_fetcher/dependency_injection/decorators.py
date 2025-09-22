"""Dependency injection decorators."""

import logging
import functools
import inspect
from typing import Type, TypeVar, Optional, Any, Callable, Dict, List
from .container import DIContainer, get_container, ServiceScope

logger = logging.getLogger(__name__)

T = TypeVar('T')


def injectable(cls: Type[T]) -> Type[T]:
    """Mark a class as injectable.

    This decorator adds metadata to help with dependency injection
    and enables automatic constructor injection.

    Args:
        cls: Class to mark as injectable

    Returns:
        Decorated class
    """
    # Add injectable marker
    setattr(cls, '_di_injectable', True)

    # Store original constructor
    original_init = cls.__init__

    @functools.wraps(original_init)
    def new_init(self, *args, **kwargs):
        # Get container
        container = get_container()

        # Get constructor signature
        sig = inspect.signature(original_init)

        # Auto-inject dependencies for parameters without provided values
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # Skip if value already provided
            if param_name in kwargs:
                continue

            # Skip if no type annotation
            if param.annotation == param.empty:
                continue

            # Try to resolve dependency
            try:
                dependency = container.get(param.annotation)
                kwargs[param_name] = dependency
                logger.debug(f"Auto-injected {param.annotation.__name__} into {cls.__name__}")
            except Exception as e:
                # Use default value if available
                if param.default != param.empty:
                    continue
                else:
                    logger.warning(f"Failed to inject {param.annotation.__name__} into {cls.__name__}: {e}")

        # Call original constructor
        original_init(self, *args, **kwargs)

    # Replace constructor
    cls.__init__ = new_init

    logger.debug(f"Marked {cls.__name__} as injectable")
    return cls


def inject(**dependencies: Type) -> Callable:
    """Inject dependencies into function parameters.

    Args:
        **dependencies: Parameter name to type mappings for injection

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()

            # Inject specified dependencies
            for param_name, param_type in dependencies.items():
                if param_name not in kwargs:
                    try:
                        dependency = container.get(param_type)
                        kwargs[param_name] = dependency
                        logger.debug(f"Injected {param_type.__name__} as {param_name}")
                    except Exception as e:
                        logger.warning(f"Failed to inject {param_type.__name__} as {param_name}: {e}")

            return func(*args, **kwargs)

        return wrapper
    return decorator


def service(
    interface: Optional[Type] = None,
    scope: ServiceScope = ServiceScope.TRANSIENT,
    container: Optional[DIContainer] = None
) -> Callable[[Type[T]], Type[T]]:
    """Register a class as a service.

    Args:
        interface: Interface type to register (defaults to the class itself)
        scope: Service scope (singleton, transient, scoped)
        container: DI container to register with (defaults to global container)

    Returns:
        Class decorator
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Get container
        target_container = container or get_container()

        # Determine service type
        service_type = interface or cls

        # Register service
        with target_container.bind(service_type).to(cls) as binding:
            if scope == ServiceScope.SINGLETON:
                binding.as_singleton()
            elif scope == ServiceScope.SCOPED:
                binding.as_scoped()
            else:
                binding.as_transient()

        # Mark as injectable
        if not hasattr(cls, '_di_injectable'):
            cls = injectable(cls)

        logger.info(f"Registered service {cls.__name__} as {service_type.__name__} with scope {scope.value}")
        return cls

    return decorator


def singleton(
    interface: Optional[Type] = None,
    container: Optional[DIContainer] = None
) -> Callable[[Type[T]], Type[T]]:
    """Register a class as a singleton service.

    Args:
        interface: Interface type to register (defaults to the class itself)
        container: DI container to register with (defaults to global container)

    Returns:
        Class decorator
    """
    return service(interface, ServiceScope.SINGLETON, container)


def transient(
    interface: Optional[Type] = None,
    container: Optional[DIContainer] = None
) -> Callable[[Type[T]], Type[T]]:
    """Register a class as a transient service.

    Args:
        interface: Interface type to register (defaults to the class itself)
        container: DI container to register with (defaults to global container)

    Returns:
        Class decorator
    """
    return service(interface, ServiceScope.TRANSIENT, container)


def scoped(
    interface: Optional[Type] = None,
    container: Optional[DIContainer] = None
) -> Callable[[Type[T]], Type[T]]:
    """Register a class as a scoped service.

    Args:
        interface: Interface type to register (defaults to the class itself)
        container: DI container to register with (defaults to global container)

    Returns:
        Class decorator
    """
    return service(interface, ServiceScope.SCOPED, container)


def auto_wire(func: Callable) -> Callable:
    """Auto-wire function dependencies based on type annotations.

    Args:
        func: Function to auto-wire

    Returns:
        Auto-wired function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        container = get_container()
        sig = inspect.signature(func)

        # Get parameter types from annotations
        for param_name, param in sig.parameters.items():
            # Skip if value already provided
            if param_name in kwargs:
                continue

            # Skip if no type annotation
            if param.annotation == param.empty:
                continue

            # Skip basic types
            if param.annotation in (str, int, float, bool, bytes):
                continue

            # Try to resolve dependency
            try:
                dependency = container.get(param.annotation)
                kwargs[param_name] = dependency
                logger.debug(f"Auto-wired {param.annotation.__name__} as {param_name}")
            except Exception as e:
                # Use default value if available
                if param.default != param.empty:
                    continue
                else:
                    logger.warning(f"Failed to auto-wire {param.annotation.__name__} as {param_name}: {e}")

        return func(*args, **kwargs)

    return wrapper


def factory(
    service_type: Type[T],
    scope: ServiceScope = ServiceScope.TRANSIENT,
    container: Optional[DIContainer] = None
) -> Callable[[Callable], Callable]:
    """Register a function as a service factory.

    Args:
        service_type: Type of service to create
        scope: Service scope
        container: DI container to register with

    Returns:
        Factory decorator
    """
    def decorator(factory_func: Callable) -> Callable:
        target_container = container or get_container()

        # Register factory
        with target_container.bind(service_type).to_factory(factory_func) as binding:
            if scope == ServiceScope.SINGLETON:
                binding.as_singleton()
            elif scope == ServiceScope.SCOPED:
                binding.as_scoped()
            else:
                binding.as_transient()

        logger.info(f"Registered factory for {service_type.__name__} with scope {scope.value}")
        return factory_func

    return decorator


def configure_services(container: Optional[DIContainer] = None) -> Callable:
    """Decorator for service configuration functions.

    Args:
        container: DI container to configure

    Returns:
        Configuration decorator
    """
    def decorator(config_func: Callable[[DIContainer], None]) -> Callable:
        target_container = container or get_container()

        # Execute configuration
        config_func(target_container)

        logger.info(f"Applied service configuration from {config_func.__name__}")
        return config_func

    return decorator


def lazy_inject(service_type: Type[T]) -> Callable:
    """Create a lazy injection wrapper.

    Args:
        service_type: Type of service to inject lazily

    Returns:
        Lazy injection wrapper
    """
    class LazyService:
        def __init__(self):
            self._service: Optional[T] = None
            self._container = get_container()

        def __getattr__(self, name: str) -> Any:
            if self._service is None:
                self._service = self._container.get(service_type)
            return getattr(self._service, name)

        def __call__(self, *args, **kwargs) -> Any:
            if self._service is None:
                self._service = self._container.get(service_type)
            return self._service(*args, **kwargs)

    return LazyService()


class Inject:
    """Property descriptor for dependency injection."""

    def __init__(self, service_type: Type[T], optional: bool = False):
        """Initialize injection descriptor.

        Args:
            service_type: Type of service to inject
            optional: Whether injection is optional
        """
        self.service_type = service_type
        self.optional = optional
        self.name = None

    def __set_name__(self, owner: Type, name: str) -> None:
        """Set descriptor name."""
        self.name = name

    def __get__(self, instance: Any, owner: Type) -> T:
        """Get injected service."""
        if instance is None:
            return self

        # Check if already injected
        attr_name = f'_injected_{self.name}'
        if hasattr(instance, attr_name):
            return getattr(instance, attr_name)

        # Inject service
        container = get_container()

        try:
            service = container.get(self.service_type)
            setattr(instance, attr_name, service)
            logger.debug(f"Injected {self.service_type.__name__} into {owner.__name__}.{self.name}")
            return service
        except Exception as e:
            if self.optional:
                logger.debug(f"Optional injection failed for {self.service_type.__name__}: {e}")
                return None
            else:
                raise

    def __set__(self, instance: Any, value: T) -> None:
        """Set injected service (override)."""
        attr_name = f'_injected_{self.name}'
        setattr(instance, attr_name, value)


def injected(service_type: Type[T], optional: bool = False) -> T:
    """Create an injection property descriptor.

    Args:
        service_type: Type of service to inject
        optional: Whether injection is optional

    Returns:
        Injection descriptor
    """
    return Inject(service_type, optional)

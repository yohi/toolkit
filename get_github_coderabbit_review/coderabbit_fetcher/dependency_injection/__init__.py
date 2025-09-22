"""Dependency injection module for CodeRabbit fetcher."""

from .container import (
    DIContainer,
    ServiceScope,
    ServiceBinding,
    ServiceProvider,
    DIError
)

from .decorators import (
    injectable,
    inject,
    service,
    singleton,
    transient,
    scoped
)

from .providers import (
    AbstractProvider,
    ClassProvider,
    FactoryProvider,
    InstanceProvider,
    ValueProvider
)

__all__ = [
    # Container
    "DIContainer",
    "ServiceScope",
    "ServiceBinding",
    "ServiceProvider",
    "DIError",

    # Decorators
    "injectable",
    "inject",
    "service",
    "singleton",
    "transient",
    "scoped",

    # Providers
    "AbstractProvider",
    "ClassProvider",
    "FactoryProvider",
    "InstanceProvider",
    "ValueProvider"
]

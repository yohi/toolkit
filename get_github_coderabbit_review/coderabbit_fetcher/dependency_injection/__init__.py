"""Dependency injection module for CodeRabbit fetcher."""

from .container import DIContainer, DIError, ServiceBinding, ServiceProvider, ServiceScope
from .decorators import inject, injectable, scoped, service, singleton, transient
from .providers import (
    AbstractProvider,
    ClassProvider,
    FactoryProvider,
    InstanceProvider,
    ValueProvider,
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
    "ValueProvider",
]

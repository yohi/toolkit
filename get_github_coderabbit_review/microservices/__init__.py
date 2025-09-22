"""Microservices architecture for CodeRabbit fetcher."""

from .service_registry import (
    ServiceRegistry,
    ServiceInstance,
    ServiceDiscovery,
    HealthCheckManager
)

from .api_gateway import (
    APIGateway,
    GatewayConfig,
    RouteConfig,
    LoadBalancer,
    RateLimiter
)

from .service_mesh import (
    ServiceMesh,
    ServiceCommunication,
    CircuitBreaker,
    RetryPolicy
)

from .orchestration import (
    ServiceOrchestrator,
    DeploymentManager,
    ConfigManager,
    SecretManager
)

__all__ = [
    # Service Registry
    "ServiceRegistry",
    "ServiceInstance",
    "ServiceDiscovery",
    "HealthCheckManager",

    # API Gateway
    "APIGateway",
    "GatewayConfig",
    "RouteConfig",
    "LoadBalancer",
    "RateLimiter",

    # Service Mesh
    "ServiceMesh",
    "ServiceCommunication",
    "CircuitBreaker",
    "RetryPolicy",

    # Orchestration
    "ServiceOrchestrator",
    "DeploymentManager",
    "ConfigManager",
    "SecretManager"
]

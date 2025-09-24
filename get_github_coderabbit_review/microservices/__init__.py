"""Microservices architecture for CodeRabbit fetcher."""

from .api_gateway import APIGateway, GatewayConfig, LoadBalancer, RateLimiter, RouteConfig
from .orchestration import ConfigManager, DeploymentManager, SecretManager, ServiceOrchestrator
from .service_mesh import CircuitBreaker, RetryPolicy, ServiceCommunication, ServiceMesh
from .service_registry import HealthCheckManager, ServiceDiscovery, ServiceInstance, ServiceRegistry

__all__ = [
    # API Gateway
    "APIGateway",
    "GatewayConfig",
    "LoadBalancer",
    "RateLimiter",
    "RouteConfig",
    # Orchestration
    "ConfigManager",
    "DeploymentManager",
    "SecretManager",
    "ServiceOrchestrator",
    # Service Mesh
    "CircuitBreaker",
    "RetryPolicy",
    "ServiceCommunication",
    "ServiceMesh",
    # Service Registry
    "HealthCheckManager",
    "ServiceDiscovery",
    "ServiceInstance",
    "ServiceRegistry",
]

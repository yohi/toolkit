"""Microservices architecture for CodeRabbit fetcher."""

from .api_gateway import APIGateway, GatewayConfig, LoadBalancer, RateLimiter, RouteConfig
from .orchestration import ConfigManager, DeploymentManager, SecretManager, ServiceOrchestrator
from .service_mesh import CircuitBreaker, RetryPolicy, ServiceCommunication, ServiceMesh
from .service_registry import HealthCheckManager, ServiceDiscovery, ServiceInstance, ServiceRegistry

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
    "SecretManager",
]

"""API Gateway for microservices architecture."""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from collections import defaultdict, deque
import threading

# Optional dependencies
try:
    from fastapi import FastAPI, Request, Response, HTTPException, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None

from ..patterns.observer import publish_event, EventType

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategy enumeration."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    HEALTH_BASED = "health_based"


@dataclass
class ServiceInstance:
    """Service instance configuration."""
    service_name: str
    instance_id: str
    host: str
    port: int
    health_check_url: str = "/health"
    weight: int = 1
    max_connections: int = 100
    current_connections: int = 0
    healthy: bool = True
    last_health_check: float = 0.0
    response_time_avg: float = 0.0
    error_count: int = 0

    @property
    def base_url(self) -> str:
        """Get base URL for the service instance."""
        return f"http://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'service_name': self.service_name,
            'instance_id': self.instance_id,
            'host': self.host,
            'port': self.port,
            'healthy': self.healthy,
            'weight': self.weight,
            'current_connections': self.current_connections,
            'max_connections': self.max_connections,
            'response_time_avg': self.response_time_avg,
            'error_count': self.error_count
        }


@dataclass
class RouteConfig:
    """Route configuration for API Gateway."""
    path: str
    service_name: str
    methods: List[str] = field(default_factory=lambda: ["GET"])
    strip_prefix: bool = True
    timeout_seconds: int = 30
    retry_attempts: int = 3
    rate_limit_rpm: Optional[int] = None
    auth_required: bool = False
    cache_ttl_seconds: Optional[int] = None

    def matches_path(self, request_path: str) -> bool:
        """Check if route matches request path."""
        if self.path.endswith("/*"):
            # Wildcard matching
            prefix = self.path[:-2]
            return request_path.startswith(prefix)
        else:
            # Exact matching
            return request_path == self.path


@dataclass
class GatewayConfig:
    """API Gateway configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    enable_cors: bool = True
    enable_gzip: bool = True
    enable_metrics: bool = True
    rate_limit_enabled: bool = True
    circuit_breaker_enabled: bool = True
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    health_check_interval: int = 30
    max_retries: int = 3
    timeout_seconds: int = 30
    jwt_secret: Optional[str] = None


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self):
        """Initialize rate limiter."""
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str, limit_rpm: int) -> bool:
        """Check if request is allowed based on rate limit.

        Args:
            client_id: Client identifier
            limit_rpm: Requests per minute limit

        Returns:
            True if request is allowed
        """
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        with self.lock:
            # Clean old requests
            client_requests = self.requests[client_id]
            while client_requests and client_requests[0] < window_start:
                client_requests.popleft()

            # Check limit
            if len(client_requests) >= limit_rpm:
                return False

            # Add current request
            client_requests.append(current_time)
            return True

    def get_remaining_requests(self, client_id: str, limit_rpm: int) -> int:
        """Get remaining requests for client.

        Args:
            client_id: Client identifier
            limit_rpm: Requests per minute limit

        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        window_start = current_time - 60

        with self.lock:
            client_requests = self.requests[client_id]
            # Count requests in current window
            current_count = sum(1 for req_time in client_requests if req_time >= window_start)
            return max(0, limit_rpm - current_count)


class LoadBalancer:
    """Load balancer for service instances."""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        """Initialize load balancer.

        Args:
            strategy: Load balancing strategy
        """
        self.strategy = strategy
        self.service_instances: Dict[str, List[ServiceInstance]] = {}
        self.round_robin_counters: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()

    def register_instance(self, instance: ServiceInstance) -> None:
        """Register service instance.

        Args:
            instance: Service instance to register
        """
        with self.lock:
            if instance.service_name not in self.service_instances:
                self.service_instances[instance.service_name] = []

            # Check if instance already exists
            existing_instances = self.service_instances[instance.service_name]
            for i, existing in enumerate(existing_instances):
                if existing.instance_id == instance.instance_id:
                    existing_instances[i] = instance
                    return

            # Add new instance
            existing_instances.append(instance)
            logger.info(f"Registered service instance: {instance.service_name}:{instance.instance_id}")

    def unregister_instance(self, service_name: str, instance_id: str) -> None:
        """Unregister service instance.

        Args:
            service_name: Service name
            instance_id: Instance ID
        """
        with self.lock:
            if service_name in self.service_instances:
                self.service_instances[service_name] = [
                    instance for instance in self.service_instances[service_name]
                    if instance.instance_id != instance_id
                ]
                logger.info(f"Unregistered service instance: {service_name}:{instance_id}")

    def select_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """Select service instance based on load balancing strategy.

        Args:
            service_name: Service name

        Returns:
            Selected service instance or None
        """
        with self.lock:
            instances = self.service_instances.get(service_name, [])
            healthy_instances = [inst for inst in instances if inst.healthy]

            if not healthy_instances:
                logger.warning(f"No healthy instances available for service: {service_name}")
                return None

            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_select(service_name, healthy_instances)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_select(healthy_instances)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_select(service_name, healthy_instances)
            elif self.strategy == LoadBalancingStrategy.RANDOM:
                return self._random_select(healthy_instances)
            elif self.strategy == LoadBalancingStrategy.HEALTH_BASED:
                return self._health_based_select(healthy_instances)
            else:
                return healthy_instances[0]

    def _round_robin_select(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round robin selection."""
        counter = self.round_robin_counters[service_name]
        selected = instances[counter % len(instances)]
        self.round_robin_counters[service_name] = counter + 1
        return selected

    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least connections selection."""
        return min(instances, key=lambda x: x.current_connections)

    def _weighted_round_robin_select(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round robin selection."""
        # Simple weighted selection based on instance weights
        total_weight = sum(inst.weight for inst in instances)
        if total_weight == 0:
            return instances[0]

        counter = self.round_robin_counters[service_name]
        weight_sum = 0

        for instance in instances:
            weight_sum += instance.weight
            if counter % total_weight < weight_sum:
                self.round_robin_counters[service_name] = counter + 1
                return instance

        return instances[0]

    def _random_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Random selection."""
        import random
        return random.choice(instances)

    def _health_based_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Health-based selection (lowest response time)."""
        return min(instances, key=lambda x: x.response_time_avg or float('inf'))

    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """Get service statistics.

        Args:
            service_name: Service name

        Returns:
            Service statistics
        """
        with self.lock:
            instances = self.service_instances.get(service_name, [])
            healthy_count = sum(1 for inst in instances if inst.healthy)

            return {
                'service_name': service_name,
                'total_instances': len(instances),
                'healthy_instances': healthy_count,
                'unhealthy_instances': len(instances) - healthy_count,
                'instances': [inst.to_dict() for inst in instances]
            }


class CircuitBreaker:
    """Circuit breaker for service calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 3
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures to open circuit
            timeout_seconds: Timeout before trying again
            success_threshold: Number of successes to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.failure_counts: Dict[str, int] = defaultdict(int)
        self.last_failure_times: Dict[str, float] = {}
        self.success_counts: Dict[str, int] = defaultdict(int)
        self.circuit_states: Dict[str, str] = defaultdict(lambda: "closed")  # closed, open, half-open
        self.lock = threading.Lock()

    def call_allowed(self, service_name: str) -> bool:
        """Check if call is allowed.

        Args:
            service_name: Service name

        Returns:
            True if call is allowed
        """
        with self.lock:
            current_time = time.time()
            state = self.circuit_states[service_name]

            if state == "closed":
                return True
            elif state == "open":
                # Check if timeout has passed
                last_failure = self.last_failure_times.get(service_name, 0)
                if current_time - last_failure >= self.timeout_seconds:
                    self.circuit_states[service_name] = "half-open"
                    self.success_counts[service_name] = 0
                    return True
                return False
            elif state == "half-open":
                return True

            return False

    def record_success(self, service_name: str) -> None:
        """Record successful call.

        Args:
            service_name: Service name
        """
        with self.lock:
            state = self.circuit_states[service_name]

            if state == "half-open":
                self.success_counts[service_name] += 1
                if self.success_counts[service_name] >= self.success_threshold:
                    self.circuit_states[service_name] = "closed"
                    self.failure_counts[service_name] = 0
                    logger.info(f"Circuit breaker closed for service: {service_name}")
            else:
                self.failure_counts[service_name] = 0

    def record_failure(self, service_name: str) -> None:
        """Record failed call.

        Args:
            service_name: Service name
        """
        with self.lock:
            self.failure_counts[service_name] += 1
            self.last_failure_times[service_name] = time.time()

            if self.failure_counts[service_name] >= self.failure_threshold:
                self.circuit_states[service_name] = "open"
                logger.warning(f"Circuit breaker opened for service: {service_name}")

    def get_circuit_state(self, service_name: str) -> str:
        """Get circuit state for service.

        Args:
            service_name: Service name

        Returns:
            Circuit state (closed/open/half-open)
        """
        return self.circuit_states[service_name]


class APIGateway:
    """API Gateway for microservices."""

    def __init__(self, config: GatewayConfig):
        """Initialize API Gateway.

        Args:
            config: Gateway configuration
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for API Gateway. Install with: pip install fastapi uvicorn")

        self.config = config
        self.app = FastAPI(title="CodeRabbit API Gateway", version="1.0.0")
        self.load_balancer = LoadBalancer(config.load_balancing_strategy)
        self.rate_limiter = RateLimiter()
        self.circuit_breaker = CircuitBreaker()
        self.routes: List[RouteConfig] = []

        # Request cache
        self.request_cache: Dict[str, Tuple[Any, float]] = {}

        # Metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0,
            'cached_requests': 0,
            'circuit_breaker_opens': 0
        }

        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup FastAPI middleware."""
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )

        if self.config.enable_gzip:
            self.app.add_middleware(GZipMiddleware, minimum_size=1000)

    def _setup_routes(self) -> None:
        """Setup API Gateway routes."""

        @self.app.get("/gateway/health")
        async def gateway_health():
            """Gateway health check."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "services": {
                    service_name: self.load_balancer.get_service_stats(service_name)
                    for service_name in self.load_balancer.service_instances.keys()
                }
            }

        @self.app.get("/gateway/metrics")
        async def gateway_metrics():
            """Gateway metrics."""
            return {
                "metrics": self.metrics,
                "services": {
                    service_name: self.load_balancer.get_service_stats(service_name)
                    for service_name in self.load_balancer.service_instances.keys()
                }
            }

        @self.app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def proxy_request(request: Request, path: str):
            """Proxy request to appropriate service."""
            return await self._handle_request(request, f"/{path}")

    def add_route(self, route: RouteConfig) -> None:
        """Add route configuration.

        Args:
            route: Route configuration
        """
        self.routes.append(route)
        logger.info(f"Added route: {route.path} -> {route.service_name}")

    def register_service(self, instance: ServiceInstance) -> None:
        """Register service instance.

        Args:
            instance: Service instance
        """
        self.load_balancer.register_instance(instance)

    async def _handle_request(self, request: Request, path: str) -> Response:
        """Handle incoming request.

        Args:
            request: FastAPI request
            path: Request path

        Returns:
            Response from service
        """
        self.metrics['total_requests'] += 1
        start_time = time.time()

        try:
            # Find matching route
            route = self._find_route(path, request.method)
            if not route:
                raise HTTPException(status_code=404, detail="Route not found")

            # Check rate limiting
            if route.rate_limit_rpm and self.config.rate_limit_enabled:
                client_id = self._get_client_id(request)
                if not self.rate_limiter.is_allowed(client_id, route.rate_limit_rpm):
                    self.metrics['rate_limited_requests'] += 1
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")

            # Check authentication
            if route.auth_required:
                await self._verify_auth(request)

            # Check cache
            if route.cache_ttl_seconds:
                cache_key = self._generate_cache_key(request, path)
                cached_response = self._get_cached_response(cache_key, route.cache_ttl_seconds)
                if cached_response:
                    self.metrics['cached_requests'] += 1
                    return cached_response

            # Check circuit breaker
            if self.config.circuit_breaker_enabled:
                if not self.circuit_breaker.call_allowed(route.service_name):
                    self.metrics['circuit_breaker_opens'] += 1
                    raise HTTPException(status_code=503, detail="Service temporarily unavailable")

            # Select service instance
            instance = self.load_balancer.select_instance(route.service_name)
            if not instance:
                raise HTTPException(status_code=503, detail="No healthy service instances available")

            # Forward request
            response = await self._forward_request(request, route, instance, path)

            # Cache response
            if route.cache_ttl_seconds and response.status_code == 200:
                cache_key = self._generate_cache_key(request, path)
                self._cache_response(cache_key, response)

            # Record success
            if self.config.circuit_breaker_enabled:
                self.circuit_breaker.record_success(route.service_name)

            self.metrics['successful_requests'] += 1

            # Publish metrics event
            publish_event(
                EventType.PROCESSING_COMPLETED,
                source="APIGateway",
                data={
                    'path': path,
                    'service': route.service_name,
                    'instance': instance.instance_id,
                    'response_time_ms': (time.time() - start_time) * 1000,
                    'status_code': response.status_code
                }
            )

            return response

        except HTTPException:
            raise
        except Exception as e:
            self.metrics['failed_requests'] += 1

            # Record failure in circuit breaker
            if 'route' in locals() and self.config.circuit_breaker_enabled:
                self.circuit_breaker.record_failure(route.service_name)

            # Publish error event
            publish_event(
                EventType.PROCESSING_FAILED,
                source="APIGateway",
                data={
                    'path': path,
                    'error': str(e),
                    'response_time_ms': (time.time() - start_time) * 1000
                },
                severity="error"
            )

            logger.error(f"Request handling error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def _find_route(self, path: str, method: str) -> Optional[RouteConfig]:
        """Find matching route configuration.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Matching route configuration
        """
        for route in self.routes:
            if route.matches_path(path) and method in route.methods:
                return route
        return None

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting.

        Args:
            request: FastAPI request

        Returns:
            Client identifier
        """
        # Use IP address as client ID (in production, use more sophisticated method)
        return request.client.host if request.client else "unknown"

    async def _verify_auth(self, request: Request) -> None:
        """Verify request authentication.

        Args:
            request: FastAPI request
        """
        # Simple JWT verification (in production, use proper JWT library)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")

        token = auth_header[7:]  # Remove "Bearer " prefix
        # TODO: Implement proper JWT verification
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token")

    def _generate_cache_key(self, request: Request, path: str) -> str:
        """Generate cache key for request.

        Args:
            request: FastAPI request
            path: Request path

        Returns:
            Cache key
        """
        # Include method, path, and query parameters in cache key
        query_string = str(request.url.query)
        cache_data = f"{request.method}:{path}:{query_string}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str, ttl_seconds: int) -> Optional[Response]:
        """Get cached response if valid.

        Args:
            cache_key: Cache key
            ttl_seconds: Time to live in seconds

        Returns:
            Cached response or None
        """
        if cache_key in self.request_cache:
            response, timestamp = self.request_cache[cache_key]
            if time.time() - timestamp < ttl_seconds:
                return response
            else:
                del self.request_cache[cache_key]

        return None

    def _cache_response(self, cache_key: str, response: Response) -> None:
        """Cache response.

        Args:
            cache_key: Cache key
            response: Response to cache
        """
        self.request_cache[cache_key] = (response, time.time())

    async def _forward_request(
        self,
        request: Request,
        route: RouteConfig,
        instance: ServiceInstance,
        path: str
    ) -> Response:
        """Forward request to service instance.

        Args:
            request: Original request
            route: Route configuration
            instance: Target service instance
            path: Request path

        Returns:
            Service response
        """
        import httpx

        # Prepare target URL
        target_path = path
        if route.strip_prefix and route.path != "/" and path.startswith(route.path):
            target_path = path[len(route.path):]

        target_url = f"{instance.base_url}{target_path}"

        # Prepare headers
        headers = dict(request.headers)
        headers.pop("host", None)  # Remove host header

        # Get request body
        body = await request.body()

        # Make request to service
        async with httpx.AsyncClient(timeout=route.timeout_seconds) as client:
            service_response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params)
            )

        # Create response
        response = Response(
            content=service_response.content,
            status_code=service_response.status_code,
            headers=dict(service_response.headers)
        )

        return response

    def start(self) -> None:
        """Start API Gateway server."""
        logger.info(f"Starting API Gateway on {self.config.host}:{self.config.port}")

        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics.

        Returns:
            Gateway statistics
        """
        return {
            'config': {
                'host': self.config.host,
                'port': self.config.port,
                'load_balancing_strategy': self.config.load_balancing_strategy.value
            },
            'metrics': self.metrics,
            'routes': [
                {
                    'path': route.path,
                    'service_name': route.service_name,
                    'methods': route.methods
                }
                for route in self.routes
            ],
            'services': {
                service_name: self.load_balancer.get_service_stats(service_name)
                for service_name in self.load_balancer.service_instances.keys()
            }
        }


# Factory function
def create_api_gateway(config: Optional[GatewayConfig] = None) -> APIGateway:
    """Create API Gateway instance.

    Args:
        config: Gateway configuration

    Returns:
        API Gateway instance
    """
    if config is None:
        config = GatewayConfig()

    return APIGateway(config)


# Global API Gateway instance
_global_gateway: Optional[APIGateway] = None


def get_api_gateway() -> Optional[APIGateway]:
    """Get global API Gateway instance."""
    return _global_gateway


def set_api_gateway(gateway: APIGateway) -> None:
    """Set global API Gateway instance."""
    global _global_gateway
    _global_gateway = gateway
    logger.info("Set global API Gateway")


# Example usage
if __name__ == "__main__":
    # Create gateway configuration
    config = GatewayConfig(
        host="0.0.0.0",
        port=8000,
        enable_cors=True,
        rate_limit_enabled=True
    )

    # Create and configure gateway
    gateway = create_api_gateway(config)

    # Add routes
    gateway.add_route(RouteConfig(
        path="/api/analysis/*",
        service_name="analysis-service",
        methods=["GET", "POST"],
        rate_limit_rpm=100
    ))

    gateway.add_route(RouteConfig(
        path="/api/comments/*",
        service_name="comment-service",
        methods=["GET", "POST", "PUT"],
        auth_required=True,
        cache_ttl_seconds=300
    ))

    # Register service instances
    gateway.register_service(ServiceInstance(
        service_name="analysis-service",
        instance_id="analysis-1",
        host="localhost",
        port=8001
    ))

    gateway.register_service(ServiceInstance(
        service_name="comment-service",
        instance_id="comment-1",
        host="localhost",
        port=8002
    ))

    # Start gateway
    gateway.start()

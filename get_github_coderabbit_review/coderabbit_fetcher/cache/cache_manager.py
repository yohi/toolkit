"""Cache management system for CodeRabbit fetcher."""

import hashlib
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class CacheKey:
    """Cache key structure for namespaced cache entries.

    Provides hierarchical organization with namespace, identifier, and version.
    """

    namespace: str
    identifier: str
    version: str = "1.0"

    def to_string(self) -> str:
        """Convert to string representation."""
        return f"{self.namespace}:{self.identifier}:{self.version}"

    def to_hash(self) -> str:
        """Convert to hash representation."""
        content = f"{self.namespace}:{self.identifier}:{self.version}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class CacheEntry:
    """Cache entry structure with comprehensive metadata and lifecycle tracking.

    Includes creation time, access patterns, and expiration management.
    """

    key: CacheKey
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def touch(self) -> None:
        """Update access information."""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def to_dict(self) -> Dict[str, Union[str, Any, int, None]]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key.to_string(),
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CacheConfig:
    """Configuration for cache management system.

    Defines TTL, size limits, and cleanup policies for cache entries.
    """

    default_ttl_seconds: int = 3600  # 1 hour
    max_entries: int = 1000
    cleanup_interval_seconds: int = 300  # 5 minutes
    eviction_policy: str = "lru"  # lru, lfu, fifo
    compression_enabled: bool = True
    encryption_enabled: bool = False
    namespace_prefix: str = "coderabbit"


class CacheError(Exception):
    """Cache-related error."""

    pass


class CacheProvider(ABC):
    """Abstract base class for cache providers."""

    @abstractmethod
    def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, entry: CacheEntry) -> bool:
        """Set value in cache."""
        pass

    @abstractmethod
    def delete(self, key: CacheKey) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    def exists(self, key: CacheKey) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class CacheManager:
    """Central cache manager with multiple provider support."""

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager.

        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        self.providers: Dict[str, CacheProvider] = {}
        self.default_provider: Optional[str] = None
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False

    def register_provider(
        self, name: str, provider: CacheProvider, is_default: bool = False
    ) -> None:
        """Register a cache provider.

        Args:
            name: Provider name
            provider: Provider instance
            is_default: Whether this is the default provider
        """
        with self._lock:
            self.providers[name] = provider
            if is_default or self.default_provider is None:
                self.default_provider = name
            logger.info(f"Registered cache provider: {name}")

    def start_cleanup(self) -> None:
        """Start automatic cleanup thread."""
        if not self._running:
            self._running = True
            self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self._cleanup_thread.start()
            logger.info("Started cache cleanup thread")

    def stop_cleanup(self) -> None:
        """Stop automatic cleanup thread."""
        if self._running:
            self._running = False
            if self._cleanup_thread:
                self._cleanup_thread.join(timeout=5)
            logger.info("Stopped cache cleanup thread")

    def _cleanup_worker(self) -> None:
        """Cleanup worker thread."""
        while self._running:
            try:
                self._cleanup_expired_entries()
                time.sleep(self.config.cleanup_interval_seconds)
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")

    def _cleanup_expired_entries(self) -> None:
        """Clean up expired entries from all providers."""
        for provider_name, _provider in self.providers.items():
            try:
                # This is a simplified approach - actual implementation would depend on provider
                logger.debug(f"Cleaning up expired entries in provider: {provider_name}")
            except Exception as e:
                logger.error(f"Error cleaning up provider {provider_name}: {e}")

    def get(
        self, key: Union[CacheKey, str], provider_name: Optional[str] = None, default: Any = None
    ) -> Any:
        """Get value from cache.

        Args:
            key: Cache key
            provider_name: Specific provider to use
            default: Default value if not found

        Returns:
            Cached value or default
        """
        try:
            if isinstance(key, str):
                key = self._parse_key_string(key)

            with self._lock:
                provider = self._get_provider(provider_name)
            entry = provider.get(key)

            if entry is None:
                with self._lock:
                    self.stats["misses"] += 1
                logger.debug(f"Cache miss for key: {key.to_string()}")
                return default

            if entry.is_expired():
                provider.delete(key)
                with self._lock:
                    self.stats["misses"] += 1
                logger.debug(f"Cache expired for key: {key.to_string()}")
                return default

            entry.touch()
            provider.set(entry)  # Update access info
            with self._lock:
                self.stats["hits"] += 1
            logger.debug(f"Cache hit for key: {key.to_string()}")

            return entry.value

        except Exception:
            with self._lock:
                self.stats["errors"] += 1
            logger.exception(f"Error getting cache key {key}")
            return default

    def set(
        self,
        key: Union[CacheKey, str],
        value: Any,
        ttl_seconds: Optional[int] = None,
        provider_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            provider_name: Specific provider to use
            metadata: Optional metadata

        Returns:
            True if successful
        """
        try:
            if isinstance(key, str):
                key = self._parse_key_string(key)

            provider = self._get_provider(provider_name)

            ttl = ttl_seconds or self.config.default_ttl_seconds
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None

            entry = CacheEntry(key=key, value=value, expires_at=expires_at, metadata=metadata or {})

            success = provider.set(entry)
            if success:
                with self._lock:
                    self.stats["sets"] += 1
                logger.debug(f"Cache set for key: {key.to_string()}")

            return success

        except Exception:
            with self._lock:
                self.stats["errors"] += 1
            logger.exception("Error setting cache key")
            return False

    def delete(self, key: Union[CacheKey, str], provider_name: Optional[str] = None) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key
            provider_name: Specific provider to use

        Returns:
            True if successful
        """
        try:
            if isinstance(key, str):
                key = self._parse_key_string(key)

            provider = self._get_provider(provider_name)
            success = provider.delete(key)

            if success:
                with self._lock:
                    self.stats["deletes"] += 1
                logger.debug(f"Cache delete for key: {key.to_string()}")

            return success

        except Exception:
            with self._lock:
                self.stats["errors"] += 1
            logger.exception("Error deleting cache key")
            return False

    def exists(self, key: Union[CacheKey, str], provider_name: Optional[str] = None) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key
            provider_name: Specific provider to use

        Returns:
            True if key exists
        """
        try:
            if isinstance(key, str):
                key = self._parse_key_string(key)

            provider = self._get_provider(provider_name)
            return provider.exists(key)

        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False

    def clear(self, provider_name: Optional[str] = None) -> bool:
        """Clear cache.

        Args:
            provider_name: Specific provider to clear, or all if None

        Returns:
            True if successful
        """
        try:
            if provider_name:
                provider = self._get_provider(provider_name)
                return provider.clear()
            else:
                # Clear all providers
                success = True
                for provider in self.providers.values():
                    success &= provider.clear()
                return success

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        stats = self.stats.copy()

        # Calculate hit rate
        total_requests = stats["hits"] + stats["misses"]
        if total_requests > 0:
            stats["hit_rate"] = stats["hits"] / total_requests
        else:
            stats["hit_rate"] = 0.0

        # Get provider stats
        provider_stats = {}
        for name, provider in self.providers.items():
            try:
                provider_stats[name] = provider.get_stats()
            except Exception as e:
                logger.error(f"Error getting stats from provider {name}: {e}")
                provider_stats[name] = {"error": str(e)}

        stats["providers"] = provider_stats
        stats["config"] = {
            "default_ttl_seconds": self.config.default_ttl_seconds,
            "max_entries": self.config.max_entries,
            "eviction_policy": self.config.eviction_policy,
        }

        return stats

    def _get_provider(self, provider_name: Optional[str] = None) -> CacheProvider:
        """Get cache provider.

        Args:
            provider_name: Provider name or None for default

        Returns:
            Cache provider instance

        Raises:
            CacheError: If provider not found
        """
        name = provider_name or self.default_provider

        if name is None:
            raise CacheError("No default cache provider configured")

        if name not in self.providers:
            raise CacheError(f"Cache provider not found: {name}")

        return self.providers[name]

    def _parse_key_string(self, key_string: str) -> CacheKey:
        """Parse key string into CacheKey.

        Args:
            key_string: Key string in format "namespace:identifier:version"

        Returns:
            CacheKey instance
        """
        parts = key_string.split(":", 2)
        if len(parts) == 1:
            return CacheKey(namespace=self.config.namespace_prefix, identifier=parts[0])
        elif len(parts) == 2:
            return CacheKey(namespace=parts[0], identifier=parts[1])
        else:
            return CacheKey(namespace=parts[0], identifier=parts[1], version=parts[2])


def cache_result(
    cache_manager: CacheManager,
    key_template: str,
    ttl_seconds: Optional[int] = None,
    namespace: str = "function_cache",
):
    """Decorator to cache function results.

    Args:
        cache_manager: Cache manager instance
        key_template: Key template with {arg_name} placeholders
        ttl_seconds: Cache TTL in seconds
        namespace: Cache namespace

    Returns:
        Decorated function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            key_data = bound_args.arguments
            key_identifier = key_template.format(**key_data)
            cache_key = CacheKey(namespace=namespace, identifier=key_identifier)

            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl_seconds=ttl_seconds)

            return result

        return wrapper

    return decorator

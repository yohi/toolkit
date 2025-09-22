"""Redis cache implementation for CodeRabbit fetcher."""

import logging
import json
import pickle
from typing import Dict, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

from .cache_manager import CacheProvider, CacheKey, CacheEntry, CacheError

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """Redis cache configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, Any] = None
    retry_on_timeout: bool = True
    decode_responses: bool = True
    max_connections: int = 50
    serialization: str = "json"  # json, pickle
    compression: bool = False
    key_prefix: str = "coderabbit:"


class RedisCache(CacheProvider):
    """Redis cache implementation."""

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize Redis cache.

        Args:
            config: Redis configuration
        """
        self.config = config or RedisConfig()
        self._redis_client = None
        self._available = False

        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'reconnects': 0
        }

        self._connect()

    def _connect(self) -> None:
        """Connect to Redis server."""
        try:
            import redis

            connection_pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                socket_keepalive=self.config.socket_keepalive,
                socket_keepalive_options=self.config.socket_keepalive_options or {},
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=self.config.decode_responses,
                max_connections=self.config.max_connections
            )

            self._redis_client = redis.Redis(connection_pool=connection_pool)

            # Test connection
            self._redis_client.ping()
            self._available = True

            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")

        except ImportError:
            logger.error("Redis library not installed. Install with: pip install redis")
            self._available = False
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._available = False

    def _ensure_connected(self) -> bool:
        """Ensure Redis connection is available."""
        if not self._available or not self._redis_client:
            self._connect()

        if not self._available:
            return False

        try:
            self._redis_client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis connection lost, attempting reconnect: {e}")
            self._connect()
            self.stats['reconnects'] += 1
            return self._available

    def _serialize_entry(self, entry: CacheEntry) -> Union[str, bytes]:
        """Serialize cache entry for storage."""
        try:
            data = {
                'key': entry.key.to_string(),
                'value': entry.value,
                'created_at': entry.created_at.isoformat(),
                'expires_at': entry.expires_at.isoformat() if entry.expires_at else None,
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed.isoformat(),
                'metadata': entry.metadata
            }

            if self.config.serialization == "pickle":
                return pickle.dumps(data)
            else:
                return json.dumps(data, default=str)

        except Exception as e:
            logger.error(f"Error serializing cache entry: {e}")
            raise CacheError(f"Serialization failed: {e}")

    def _deserialize_entry(self, data: Union[str, bytes]) -> CacheEntry:
        """Deserialize cache entry from storage."""
        try:
            if self.config.serialization == "pickle":
                entry_data = pickle.loads(data)
            else:
                entry_data = json.loads(data)

            # Parse key
            key_parts = entry_data['key'].split(':', 2)
            if len(key_parts) == 3:
                key = CacheKey(namespace=key_parts[0], identifier=key_parts[1], version=key_parts[2])
            elif len(key_parts) == 2:
                key = CacheKey(namespace=key_parts[0], identifier=key_parts[1])
            else:
                key = CacheKey(namespace="default", identifier=key_parts[0])

            # Parse timestamps
            created_at = datetime.fromisoformat(entry_data['created_at'])
            last_accessed = datetime.fromisoformat(entry_data['last_accessed'])
            expires_at = None
            if entry_data['expires_at']:
                expires_at = datetime.fromisoformat(entry_data['expires_at'])

            return CacheEntry(
                key=key,
                value=entry_data['value'],
                created_at=created_at,
                expires_at=expires_at,
                access_count=entry_data.get('access_count', 0),
                last_accessed=last_accessed,
                metadata=entry_data.get('metadata', {})
            )

        except Exception as e:
            logger.error(f"Error deserializing cache entry: {e}")
            raise CacheError(f"Deserialization failed: {e}")

    def _get_redis_key(self, key: CacheKey) -> str:
        """Get Redis key with prefix."""
        return f"{self.config.key_prefix}{key.to_string()}"

    def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """Get entry from Redis cache."""
        if not self._ensure_connected():
            self.stats['errors'] += 1
            return None

        try:
            redis_key = self._get_redis_key(key)
            data = self._redis_client.get(redis_key)

            if data is None:
                self.stats['misses'] += 1
                return None

            entry = self._deserialize_entry(data)

            # Check expiration (Redis should handle this, but double-check)
            if entry.is_expired():
                self.delete(key)
                self.stats['misses'] += 1
                return None

            # Update access information
            entry.touch()
            self.set(entry)  # Update in Redis

            self.stats['hits'] += 1
            return entry

        except Exception as e:
            logger.error(f"Error getting from Redis cache: {e}")
            self.stats['errors'] += 1
            return None

    def set(self, entry: CacheEntry) -> bool:
        """Set entry in Redis cache."""
        if not self._ensure_connected():
            self.stats['errors'] += 1
            return False

        try:
            redis_key = self._get_redis_key(entry.key)
            serialized_data = self._serialize_entry(entry)

            # Calculate TTL
            ttl = None
            if entry.expires_at:
                ttl_delta = entry.expires_at - datetime.now()
                ttl = max(1, int(ttl_delta.total_seconds()))

            # Set in Redis with TTL
            if ttl:
                self._redis_client.setex(redis_key, ttl, serialized_data)
            else:
                self._redis_client.set(redis_key, serialized_data)

            self.stats['sets'] += 1
            return True

        except Exception as e:
            logger.error(f"Error setting Redis cache: {e}")
            self.stats['errors'] += 1
            return False

    def delete(self, key: CacheKey) -> bool:
        """Delete entry from Redis cache."""
        if not self._ensure_connected():
            self.stats['errors'] += 1
            return False

        try:
            redis_key = self._get_redis_key(key)
            result = self._redis_client.delete(redis_key)

            if result > 0:
                self.stats['deletes'] += 1
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting from Redis cache: {e}")
            self.stats['errors'] += 1
            return False

    def exists(self, key: CacheKey) -> bool:
        """Check if key exists in Redis cache."""
        if not self._ensure_connected():
            return False

        try:
            redis_key = self._get_redis_key(key)
            return bool(self._redis_client.exists(redis_key))

        except Exception as e:
            logger.error(f"Error checking Redis cache existence: {e}")
            return False

    def clear(self) -> bool:
        """Clear all entries from Redis cache."""
        if not self._ensure_connected():
            self.stats['errors'] += 1
            return False

        try:
            # Get all keys with our prefix
            pattern = f"{self.config.key_prefix}*"
            keys = self._redis_client.keys(pattern)

            if keys:
                self._redis_client.delete(*keys)

            return True

        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            self.stats['errors'] += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        stats = self.stats.copy()

        # Calculate hit rate
        total_requests = stats['hits'] + stats['misses']
        if total_requests > 0:
            stats['hit_rate'] = stats['hits'] / total_requests
        else:
            stats['hit_rate'] = 0.0

        # Add Redis-specific stats
        stats['redis_available'] = self._available
        stats['config'] = {
            'host': self.config.host,
            'port': self.config.port,
            'db': self.config.db,
            'serialization': self.config.serialization,
            'compression': self.config.compression
        }

        # Get Redis server info if available
        if self._ensure_connected():
            try:
                redis_info = self._redis_client.info()
                stats['redis_info'] = {
                    'version': redis_info.get('redis_version'),
                    'used_memory': redis_info.get('used_memory'),
                    'used_memory_human': redis_info.get('used_memory_human'),
                    'connected_clients': redis_info.get('connected_clients'),
                    'total_commands_processed': redis_info.get('total_commands_processed'),
                    'uptime_in_seconds': redis_info.get('uptime_in_seconds')
                }

                # Count our keys
                pattern = f"{self.config.key_prefix}*"
                key_count = len(self._redis_client.keys(pattern))
                stats['key_count'] = key_count

            except Exception as e:
                logger.warning(f"Error getting Redis server info: {e}")
                stats['redis_info'] = {'error': str(e)}

        return stats

    def flush_namespace(self, namespace: str) -> int:
        """Flush all keys in a specific namespace.

        Args:
            namespace: Namespace to flush

        Returns:
            Number of keys deleted
        """
        if not self._ensure_connected():
            return 0

        try:
            pattern = f"{self.config.key_prefix}{namespace}:*"
            keys = self._redis_client.keys(pattern)

            if keys:
                deleted = self._redis_client.delete(*keys)
                logger.info(f"Flushed {deleted} keys from namespace: {namespace}")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Error flushing namespace {namespace}: {e}")
            return 0

    def get_namespace_keys(self, namespace: str) -> list[str]:
        """Get all keys in a specific namespace.

        Args:
            namespace: Namespace to search

        Returns:
            List of keys in the namespace
        """
        if not self._ensure_connected():
            return []

        try:
            pattern = f"{self.config.key_prefix}{namespace}:*"
            redis_keys = self._redis_client.keys(pattern)

            # Remove prefix from keys
            prefix_len = len(self.config.key_prefix)
            return [key[prefix_len:] for key in redis_keys]

        except Exception as e:
            logger.error(f"Error getting namespace keys for {namespace}: {e}")
            return []

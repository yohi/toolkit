"""In-memory cache implementation for CodeRabbit fetcher."""

import logging
import threading
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .cache_manager import CacheEntry, CacheKey, CacheProvider

logger = logging.getLogger(__name__)


@dataclass
class MemoryCacheConfig:
    """Memory cache configuration."""

    max_entries: int = 1000
    eviction_policy: str = "lru"  # lru, lfu, fifo
    cleanup_expired: bool = True
    thread_safe: bool = True


class MemoryCache(CacheProvider):
    """In-memory cache implementation with LRU/LFU/FIFO eviction."""

    def __init__(self, config: Optional[MemoryCacheConfig] = None):
        """Initialize memory cache.

        Args:
            config: Memory cache configuration
        """
        self.config = config or MemoryCacheConfig()
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU
        self._access_count: Dict[str, int] = {}  # For LFU
        self._creation_order: List[str] = []  # For FIFO

        if self.config.thread_safe:
            self._lock = threading.RLock()
        else:
            self._lock = threading.RLock()  # Always use lock for safety

        self.stats = Counter(hits=0, misses=0, sets=0, deletes=0, evictions=0, size=0)

    def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """Get entry from memory cache."""
        with self._lock:
            key_str = key.to_string()

            if key_str not in self._cache:
                self.stats["misses"] += 1
                return None

            entry = self._cache[key_str]

            # Check expiration
            if entry.is_expired():
                self._remove_entry(key_str)
                self.stats["misses"] += 1
                return None

            # Update access tracking
            self._update_access(key_str)
            self.stats["hits"] += 1

            return entry

    def set(self, entry: CacheEntry) -> bool:
        """Set entry in memory cache."""
        try:
            with self._lock:
                key_str = entry.key.to_string()

                # Check if we need to evict entries
                if key_str not in self._cache and len(self._cache) >= self.config.max_entries:
                    self._evict_entries(1)

                # Store entry
                self._cache[key_str] = entry

                # Update tracking structures
                if key_str not in self._access_order:
                    self._access_order.append(key_str)
                    self._creation_order.append(key_str)
                    self._access_count[key_str] = 0

                self._update_access(key_str)
                self.stats["sets"] += 1
                self.stats["size"] = len(self._cache)

                return True

        except Exception as e:
            logger.error(f"Error setting cache entry: {e}")
            return False

    def delete(self, key: CacheKey) -> bool:
        """Delete entry from memory cache."""
        try:
            with self._lock:
                key_str = key.to_string()

                if key_str in self._cache:
                    self._remove_entry(key_str)
                    self.stats["deletes"] += 1
                    self.stats["size"] = len(self._cache)
                    return True

                return False

        except Exception as e:
            logger.error(f"Error deleting cache entry: {e}")
            return False

    def exists(self, key: CacheKey) -> bool:
        """Check if key exists in memory cache."""
        with self._lock:
            key_str = key.to_string()

            if key_str not in self._cache:
                return False

            entry = self._cache[key_str]
            if entry.is_expired():
                self._remove_entry(key_str)
                return False

            return True

    def clear(self) -> bool:
        """Clear all entries from memory cache."""
        try:
            with self._lock:
                self._cache.clear()
                self._access_order.clear()
                self._access_count.clear()
                self._creation_order.clear()
                self.stats["size"] = 0
                return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics."""
        with self._lock:
            stats = self.stats.copy()
            stats.update(
                {
                    "current_size": len(self._cache),
                    "max_entries": self.config.max_entries,
                    "eviction_policy": self.config.eviction_policy,
                    "memory_usage_estimate": self._estimate_memory_usage(),
                }
            )

            # Calculate additional metrics
            total_requests = stats["hits"] + stats["misses"]
            if total_requests > 0:
                stats["hit_rate"] = stats["hits"] / total_requests
            else:
                stats["hit_rate"] = 0.0

            return stats

    def cleanup_expired(self) -> int:
        """Clean up expired entries.

        Returns:
            Number of expired entries removed
        """
        with self._lock:
            expired_keys = []

            for key_str, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key_str)

            for key_str in expired_keys:
                self._remove_entry(key_str)

            if expired_keys:
                self.stats["size"] = len(self._cache)
                logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def get_entries_by_namespace(self, namespace: str) -> List[CacheEntry]:
        """Get all entries for a specific namespace.

        Args:
            namespace: Namespace to filter by

        Returns:
            List of cache entries in the namespace
        """
        with self._lock:
            entries = []

            for entry in self._cache.values():
                if entry.key.namespace == namespace and not entry.is_expired():
                    entries.append(entry)

            return entries

    def evict_namespace(self, namespace: str) -> int:
        """Evict all entries from a specific namespace.

        Args:
            namespace: Namespace to evict

        Returns:
            Number of entries evicted
        """
        with self._lock:
            keys_to_evict = []

            for key_str, entry in self._cache.items():
                if entry.key.namespace == namespace:
                    keys_to_evict.append(key_str)

            for key_str in keys_to_evict:
                self._remove_entry(key_str)

            if keys_to_evict:
                self.stats["size"] = len(self._cache)
                self.stats["evictions"] += len(keys_to_evict)
                logger.debug(f"Evicted {len(keys_to_evict)} entries from namespace: {namespace}")

            return len(keys_to_evict)

    def _update_access(self, key_str: str) -> None:
        """Update access tracking for eviction policies."""
        # Update access count for LFU
        self._access_count[key_str] = self._access_count.get(key_str, 0) + 1

        # Update access order for LRU
        if key_str in self._access_order:
            self._access_order.remove(key_str)
        self._access_order.append(key_str)

    def _remove_entry(self, key_str: str) -> None:
        """Remove entry and update tracking structures."""
        if key_str in self._cache:
            del self._cache[key_str]

        if key_str in self._access_order:
            self._access_order.remove(key_str)

        if key_str in self._access_count:
            del self._access_count[key_str]

        if key_str in self._creation_order:
            self._creation_order.remove(key_str)

    def _evict_entries(self, count: int) -> None:
        """Evict entries based on eviction policy."""
        if not self._cache:
            return

        evicted = 0
        policy = self.config.eviction_policy.lower()

        while evicted < count and self._cache:
            if policy == "lru":
                # Evict least recently used
                if self._access_order:
                    key_to_evict = self._access_order[0]
                    self._remove_entry(key_to_evict)
                    evicted += 1
                else:
                    break

            elif policy == "lfu":
                # Evict least frequently used
                if self._access_count:
                    min_key = min(self._access_count, key=self._access_count.get)
                    self._remove_entry(min_key)
                    evicted += 1
                else:
                    break

            elif policy == "fifo":
                # Evict first in, first out
                if self._creation_order:
                    key_to_evict = self._creation_order[0]
                    self._remove_entry(key_to_evict)
                    evicted += 1
                else:
                    break
            else:
                # Default to LRU
                if self._access_order:
                    key_to_evict = self._access_order[0]
                    self._remove_entry(key_to_evict)
                    evicted += 1
                else:
                    break

        self.stats["evictions"] += evicted
        self.stats["size"] = len(self._cache)

        if evicted > 0:
            logger.debug(f"Evicted {evicted} entries using {policy} policy")

    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        try:
            import sys

            total_size = 0

            # Estimate cache dictionary size
            total_size += sys.getsizeof(self._cache)

            # Estimate entry sizes
            for entry in self._cache.values():
                total_size += sys.getsizeof(entry)
                total_size += sys.getsizeof(entry.value)

            # Estimate tracking structures
            total_size += sys.getsizeof(self._access_order)
            total_size += sys.getsizeof(self._access_count)
            total_size += sys.getsizeof(self._creation_order)

            return total_size

        except Exception as e:
            logger.warning(f"Error estimating memory usage: {e}")
            return 0


class LRUCache(MemoryCache):
    """LRU-specific memory cache implementation."""

    def __init__(self, max_entries: int = 1000):
        """Initialize LRU cache.

        Args:
            max_entries: Maximum number of entries
        """
        config = MemoryCacheConfig(max_entries=max_entries, eviction_policy="lru")
        super().__init__(config)


class LFUCache(MemoryCache):
    """LFU-specific memory cache implementation."""

    def __init__(self, max_entries: int = 1000):
        """Initialize LFU cache.

        Args:
            max_entries: Maximum number of entries
        """
        config = MemoryCacheConfig(max_entries=max_entries, eviction_policy="lfu")
        super().__init__(config)


class FIFOCache(MemoryCache):
    """FIFO-specific memory cache implementation."""

    def __init__(self, max_entries: int = 1000):
        """Initialize FIFO cache.

        Args:
            max_entries: Maximum number of entries
        """
        config = MemoryCacheConfig(max_entries=max_entries, eviction_policy="fifo")
        super().__init__(config)

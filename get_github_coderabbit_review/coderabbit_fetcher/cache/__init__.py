"""Caching module for CodeRabbit fetcher."""

from .cache_manager import (
    CacheManager,
    CacheKey,
    CacheEntry,
    CacheConfig,
    CacheError
)

from .redis_cache import (
    RedisCache,
    RedisConfig
)

from .memory_cache import (
    MemoryCache,
    MemoryCacheConfig
)

from .file_cache import (
    FileCache,
    FileCacheConfig
)

__all__ = [
    "CacheManager",
    "CacheKey",
    "CacheEntry",
    "CacheConfig",
    "CacheError",
    "RedisCache",
    "RedisConfig",
    "MemoryCache",
    "MemoryCacheConfig",
    "FileCache",
    "FileCacheConfig"
]

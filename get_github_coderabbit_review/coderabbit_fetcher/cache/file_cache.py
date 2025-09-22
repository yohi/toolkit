"""File-based cache implementation for CodeRabbit fetcher."""

import logging
import json
import pickle
import os
import threading
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import hashlib
import fcntl
import tempfile
import shutil

from .cache_manager import CacheProvider, CacheKey, CacheEntry, CacheError

logger = logging.getLogger(__name__)


@dataclass
class FileCacheConfig:
    """File cache configuration."""
    cache_dir: str = None  # Will default to system temp dir + "coderabbit_cache"
    max_file_size_mb: int = 100
    max_total_size_mb: int = 1000
    serialization: str = "json"  # json, pickle
    compression: bool = False
    file_mode: int = 0o644
    dir_mode: int = 0o755
    cleanup_interval_hours: int = 24
    max_files: int = 10000


class FileCache(CacheProvider):
    """File-based cache implementation."""

    def __init__(self, config: Optional[FileCacheConfig] = None):
        """Initialize file cache.

        Args:
            config: File cache configuration
        """
        self.config = config or FileCacheConfig()

        # Set default cache directory
        if self.config.cache_dir is None:
            self.config.cache_dir = os.path.join(tempfile.gettempdir(), "coderabbit_cache")

        self.cache_dir = Path(self.config.cache_dir)
        self._lock = threading.RLock()

        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'cleanups': 0
        }

        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True, mode=self.config.dir_mode)
        except Exception as e:
            logger.error(f"Failed to create cache directory {self.cache_dir}: {e}")
            raise CacheError(f"Cache directory creation failed: {e}")

    def _get_file_path(self, key: CacheKey) -> Path:
        """Get file path for cache key."""
        # Create subdirectories based on namespace for organization
        namespace_dir = self.cache_dir / key.namespace
        namespace_dir.mkdir(exist_ok=True, mode=self.config.dir_mode)

        # Use hash to create safe filename
        key_hash = key.to_hash()
        filename = f"{key_hash}.cache"

        return namespace_dir / filename

    def _serialize_entry(self, entry: CacheEntry) -> bytes:
        """Serialize cache entry for file storage."""
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
                serialized = pickle.dumps(data)
            else:
                serialized = json.dumps(data, default=str).encode('utf-8')

            # Compression if enabled
            if self.config.compression:
                import gzip
                serialized = gzip.compress(serialized)

            return serialized

        except Exception as e:
            logger.error(f"Error serializing cache entry: {e}")
            raise CacheError(f"Serialization failed: {e}")

    def _deserialize_entry(self, data: bytes) -> CacheEntry:
        """Deserialize cache entry from file storage."""
        try:
            # Decompression if enabled
            if self.config.compression:
                import gzip
                data = gzip.decompress(data)

            if self.config.serialization == "pickle":
                entry_data = pickle.loads(data)
            else:
                entry_data = json.loads(data.decode('utf-8'))

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

    def _read_file_with_lock(self, file_path: Path) -> Optional[bytes]:
        """Read file with file locking."""
        try:
            with open(file_path, 'rb') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                return f.read()
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error reading cache file {file_path}: {e}")
            return None

    def _write_file_with_lock(self, file_path: Path, data: bytes) -> bool:
        """Write file with file locking."""
        try:
            # Write to temporary file first, then rename (atomic operation)
            temp_file = file_path.with_suffix('.tmp')

            with open(temp_file, 'wb') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                f.write(data)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk

            # Atomic rename
            temp_file.rename(file_path)

            # Set file permissions
            os.chmod(file_path, self.config.file_mode)

            return True

        except Exception as e:
            logger.error(f"Error writing cache file {file_path}: {e}")
            # Clean up temporary file
            try:
                if 'temp_file' in locals() and temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass
            return False

    def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """Get entry from file cache."""
        with self._lock:
            try:
                file_path = self._get_file_path(key)

                if not file_path.exists():
                    self.stats['misses'] += 1
                    return None

                data = self._read_file_with_lock(file_path)
                if data is None:
                    self.stats['misses'] += 1
                    return None

                entry = self._deserialize_entry(data)

                # Check expiration
                if entry.is_expired():
                    self.delete(key)
                    self.stats['misses'] += 1
                    return None

                # Update access information
                entry.touch()
                self.set(entry)  # Update file with new access info

                self.stats['hits'] += 1
                return entry

            except Exception as e:
                logger.error(f"Error getting from file cache: {e}")
                self.stats['errors'] += 1
                return None

    def set(self, entry: CacheEntry) -> bool:
        """Set entry in file cache."""
        with self._lock:
            try:
                # Check file size limit
                serialized_data = self._serialize_entry(entry)
                file_size_mb = len(serialized_data) / (1024 * 1024)

                if file_size_mb > self.config.max_file_size_mb:
                    logger.warning(f"Cache entry too large: {file_size_mb:.2f}MB > {self.config.max_file_size_mb}MB")
                    return False

                # Check total cache size and cleanup if needed
                if self._should_cleanup():
                    self._cleanup_cache()

                file_path = self._get_file_path(entry.key)
                success = self._write_file_with_lock(file_path, serialized_data)

                if success:
                    self.stats['sets'] += 1

                return success

            except Exception as e:
                logger.error(f"Error setting file cache: {e}")
                self.stats['errors'] += 1
                return False

    def delete(self, key: CacheKey) -> bool:
        """Delete entry from file cache."""
        with self._lock:
            try:
                file_path = self._get_file_path(key)

                if file_path.exists():
                    file_path.unlink()
                    self.stats['deletes'] += 1
                    return True

                return False

            except Exception as e:
                logger.error(f"Error deleting from file cache: {e}")
                self.stats['errors'] += 1
                return False

    def exists(self, key: CacheKey) -> bool:
        """Check if key exists in file cache."""
        try:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                return False

            # Quick check if file is not expired by checking modification time
            # For full expiration check, would need to read and deserialize
            return True

        except Exception as e:
            logger.error(f"Error checking file cache existence: {e}")
            return False

    def clear(self) -> bool:
        """Clear all entries from file cache."""
        with self._lock:
            try:
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    self._ensure_cache_dir()
                return True

            except Exception as e:
                logger.error(f"Error clearing file cache: {e}")
                self.stats['errors'] += 1
                return False

    def get_stats(self) -> Dict[str, Any]:
        """Get file cache statistics."""
        with self._lock:
            stats = self.stats.copy()

            # Calculate hit rate
            total_requests = stats['hits'] + stats['misses']
            if total_requests > 0:
                stats['hit_rate'] = stats['hits'] / total_requests
            else:
                stats['hit_rate'] = 0.0

            # Get cache directory info
            try:
                file_count = 0
                total_size = 0
                namespace_counts = {}

                for root, dirs, files in os.walk(self.cache_dir):
                    for file in files:
                        if file.endswith('.cache'):
                            file_count += 1
                            file_path = Path(root) / file
                            file_size = file_path.stat().st_size
                            total_size += file_size

                            # Count by namespace
                            namespace = Path(root).name
                            namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1

                stats.update({
                    'file_count': file_count,
                    'total_size_bytes': total_size,
                    'total_size_mb': total_size / (1024 * 1024),
                    'namespace_counts': namespace_counts,
                    'cache_dir': str(self.cache_dir),
                    'max_files': self.config.max_files,
                    'max_total_size_mb': self.config.max_total_size_mb
                })

            except Exception as e:
                logger.error(f"Error getting cache directory stats: {e}")
                stats.update({
                    'file_count': -1,
                    'total_size_bytes': -1,
                    'error': str(e)
                })

            return stats

    def cleanup_expired(self) -> int:
        """Clean up expired entries.

        Returns:
            Number of expired entries removed
        """
        with self._lock:
            removed_count = 0

            try:
                for root, dirs, files in os.walk(self.cache_dir):
                    for file in files:
                        if file.endswith('.cache'):
                            file_path = Path(root) / file

                            try:
                                data = self._read_file_with_lock(file_path)
                                if data:
                                    entry = self._deserialize_entry(data)
                                    if entry.is_expired():
                                        file_path.unlink()
                                        removed_count += 1
                            except Exception as e:
                                logger.warning(f"Error checking expiration for {file_path}: {e}")
                                # Remove corrupted files
                                try:
                                    file_path.unlink()
                                    removed_count += 1
                                except Exception:
                                    pass

                if removed_count > 0:
                    self.stats['cleanups'] += 1
                    logger.info(f"Cleaned up {removed_count} expired/corrupted cache files")

            except Exception as e:
                logger.error(f"Error during cache cleanup: {e}")

            return removed_count

    def _should_cleanup(self) -> bool:
        """Check if cache cleanup is needed."""
        try:
            stats = self.get_stats()

            # Check file count limit
            if stats.get('file_count', 0) > self.config.max_files:
                return True

            # Check total size limit
            if stats.get('total_size_mb', 0) > self.config.max_total_size_mb:
                return True

            return False

        except Exception:
            return False

    def _cleanup_cache(self) -> None:
        """Cleanup cache by removing oldest files."""
        try:
            # Get all cache files with their modification times
            cache_files = []

            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file.endswith('.cache'):
                        file_path = Path(root) / file
                        try:
                            mtime = file_path.stat().st_mtime
                            cache_files.append((file_path, mtime))
                        except Exception:
                            # Remove inaccessible files
                            try:
                                file_path.unlink()
                            except Exception:
                                pass

            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda x: x[1])

            # Remove oldest files until we're under limits
            removed = 0
            target_file_count = int(self.config.max_files * 0.8)  # Clean to 80% of limit

            while len(cache_files) - removed > target_file_count and cache_files:
                file_path, _ = cache_files[removed]
                try:
                    file_path.unlink()
                    removed += 1
                except Exception as e:
                    logger.warning(f"Error removing cache file {file_path}: {e}")
                    removed += 1  # Count it anyway to avoid infinite loop

            if removed > 0:
                logger.info(f"Cache cleanup removed {removed} old files")
                self.stats['cleanups'] += 1

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    def clear_namespace(self, namespace: str) -> int:
        """Clear all entries from a specific namespace.

        Args:
            namespace: Namespace to clear

        Returns:
            Number of entries removed
        """
        with self._lock:
            removed_count = 0
            namespace_dir = self.cache_dir / namespace

            if namespace_dir.exists():
                try:
                    # Count files before removal
                    removed_count += sum(
                        1
                        for root, dirs, files in os.walk(namespace_dir)
                        for f in files
                        if f.endswith('.cache')
                    )
                    shutil.rmtree(namespace_dir)
                except Exception as e:
                    logger.error(f"Error clearing namespace {namespace}: {e}")

            return removed_count

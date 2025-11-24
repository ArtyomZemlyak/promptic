"""Version listing cache with directory modification time tracking."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class VersionCache(Generic[T]):
    """
    Cache for version listings with directory modification time invalidation.

    # AICODE-NOTE: This cache tracks directory modification times to automatically
    invalidate cached version listings when directories are modified. This ensures
    version resolution always reflects current filesystem state while avoiding
    repeated directory scans.
    """

    def __init__(self) -> None:
        """Initialize empty cache."""
        self._cache: Dict[str, T] = {}
        self._timestamps: Dict[str, float] = {}

    def get(self, key: str) -> Optional[T]:
        """
        Get cached value if valid.

        Args:
            key: Cache key (typically directory path, may include parameters like :recursive=True)

        Returns:
            Cached value if valid, None if not cached or invalidated
        """
        if key not in self._cache:
            return None

        # Check if directory modification time has changed
        if key in self._timestamps:
            # Extract actual directory path from key (handle parametrized keys)
            directory_path = key.split(":")[0]
            try:
                current_mtime = os.path.getmtime(directory_path)
                if current_mtime != self._timestamps[key]:
                    # Directory modified, invalidate cache
                    self.invalidate(key)
                    return None
            except OSError:
                # Directory doesn't exist or inaccessible, invalidate
                self.invalidate(key)
                return None

        return self._cache[key]

    def set(self, key: str, value: T) -> None:
        """
        Cache a value with current directory modification time.

        Args:
            key: Cache key (typically directory path, may include parameters like :recursive=True)
            value: Value to cache
        """
        self._cache[key] = value
        # Extract actual directory path from key (handle parametrized keys)
        directory_path = key.split(":")[0]
        try:
            self._timestamps[key] = os.path.getmtime(directory_path)
        except OSError:
            # If directory doesn't exist or inaccessible, don't track timestamp
            # Cache will be invalidated on next get() call
            pass

    def invalidate(self, key: str) -> None:
        """
        Invalidate cache entry for a key.

        Args:
            key: Cache key to invalidate
        """
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()

    def is_valid(self, key: str) -> bool:
        """
        Check if cache entry is valid.

        Args:
            key: Cache key to check

        Returns:
            True if cache entry exists and is valid, False otherwise
        """
        return self.get(key) is not None

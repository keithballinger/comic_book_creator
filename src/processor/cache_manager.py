"""Cache manager for storing generated panels and API responses."""

import asyncio
import json
import hashlib
import aiofiles
from pathlib import Path
from typing import Any, Dict, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of generated panels and API responses."""
    
    def __init__(
        self,
        cache_dir: str = ".cache",
        max_size_mb: int = 500,
        ttl_hours: int = 24
    ):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache storage
            max_size_mb: Maximum cache size in MB
            ttl_hours: Time to live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl = timedelta(hours=ttl_hours)
        
        # In-memory cache for fast access
        self.memory_cache: Dict[str, Any] = {}
        self.memory_cache_size = 0
        self.max_memory_size = 50 * 1024 * 1024  # 50MB in-memory cache
        
        # Cache metadata
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        # Check memory cache first
        if key in self.memory_cache:
            logger.debug(f"Memory cache hit: {key}")
            return self.memory_cache[key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check if expired
        if self._is_expired(key):
            logger.debug(f"Cache expired: {key}")
            await self.delete(key)
            return None
        
        try:
            async with aiofiles.open(cache_file, 'r') as f:
                content = await f.read()
                data = json.loads(content)
                
            # Add to memory cache
            self._add_to_memory_cache(key, data)
            
            logger.debug(f"Disk cache hit: {key}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_override: Optional[int] = None):
        """Set item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_override: Optional TTL override in hours
        """
        # Check cache size limit
        if await self._get_cache_size() > self.max_size_bytes:
            await self._cleanup_old_entries()
        
        # Save to disk
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(value, indent=2))
            
            # Update metadata
            self.metadata[key] = {
                'created': datetime.now().isoformat(),
                'ttl_hours': ttl_override or (self.ttl.total_seconds() / 3600),
                'size': cache_file.stat().st_size
            }
            self._save_metadata()
            
            # Add to memory cache
            self._add_to_memory_cache(key, value)
            
            logger.debug(f"Cached: {key}")
            
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    async def delete(self, key: str):
        """Delete item from cache.
        
        Args:
            key: Cache key
        """
        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove from disk
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            cache_file.unlink()
        
        # Remove from metadata
        if key in self.metadata:
            del self.metadata[key]
            self._save_metadata()
        
        logger.debug(f"Deleted from cache: {key}")
    
    async def clear(self):
        """Clear all cache entries."""
        # Clear memory cache
        self.memory_cache.clear()
        self.memory_cache_size = 0
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name != "cache_metadata.json":
                cache_file.unlink()
        
        # Clear metadata
        self.metadata.clear()
        self._save_metadata()
        
        logger.info("Cache cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        total_size = await self._get_cache_size()
        
        return {
            'total_entries': len(self.metadata),
            'memory_entries': len(self.memory_cache),
            'total_size_mb': total_size / (1024 * 1024),
            'memory_size_mb': self.memory_cache_size / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'cache_dir': str(self.cache_dir),
        }
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk.
        
        Returns:
            Metadata dictionary
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        
        return {}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired.
        
        Args:
            key: Cache key
            
        Returns:
            True if expired
        """
        if key not in self.metadata:
            return True
        
        entry = self.metadata[key]
        created = datetime.fromisoformat(entry['created'])
        ttl = timedelta(hours=entry.get('ttl_hours', 24))
        
        return datetime.now() > created + ttl
    
    def _add_to_memory_cache(self, key: str, value: Any):
        """Add item to memory cache with size management.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Estimate size (rough approximation)
        size = len(json.dumps(value))
        
        # Check if it fits in memory cache
        if size > self.max_memory_size:
            return  # Too large for memory cache
        
        # Make room if needed
        while self.memory_cache_size + size > self.max_memory_size and self.memory_cache:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(self.memory_cache))
            oldest_size = len(json.dumps(self.memory_cache[oldest_key]))
            del self.memory_cache[oldest_key]
            self.memory_cache_size -= oldest_size
        
        # Add to cache
        self.memory_cache[key] = value
        self.memory_cache_size += size
    
    async def _get_cache_size(self) -> int:
        """Get total cache size in bytes.
        
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        for key, entry in self.metadata.items():
            total_size += entry.get('size', 0)
        
        return total_size
    
    async def _cleanup_old_entries(self):
        """Clean up old cache entries to make room."""
        # Sort by creation time
        sorted_entries = sorted(
            self.metadata.items(),
            key=lambda x: x[1]['created']
        )
        
        # Remove oldest entries until we're under 80% of max size
        target_size = int(self.max_size_bytes * 0.8)
        current_size = await self._get_cache_size()
        
        for key, entry in sorted_entries:
            if current_size <= target_size:
                break
            
            await self.delete(key)
            current_size -= entry.get('size', 0)
        
        logger.info(f"Cleaned up cache to {current_size / (1024*1024):.1f}MB")
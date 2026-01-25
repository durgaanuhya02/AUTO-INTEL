"""
Caching utilities for improved performance
"""
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import redis.asyncio as redis
from ..core.database import get_redis

class CacheManager:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.default_ttl = 300  # 5 minutes

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            self.redis_client = await get_redis()
        
        try:
            cached_value = await self.redis_client.get(f"cache:{key}")
            if cached_value:
                return json.loads(cached_value)
        except Exception:
            pass
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            self.redis_client = await get_redis()
        
        try:
            ttl = ttl or self.default_ttl
            await self.redis_client.set(
                f"cache:{key}",
                json.dumps(value, default=str),
                ex=ttl
            )
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            self.redis_client = await get_redis()
        
        try:
            await self.redis_client.delete(f"cache:{key}")
            return True
        except Exception:
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            self.redis_client = await get_redis()
        
        try:
            keys = await self.redis_client.keys(f"cache:{pattern}")
            if keys:
                return await self.redis_client.delete(*keys)
        except Exception:
            pass
        return 0

# Global cache manager instance
cache_manager = CacheManager()

def cache_result(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            
            # Add args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                else:
                    key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
            
            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}:{v}")
                else:
                    key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

class MetricsCache:
    """Specialized cache for metrics data"""
    
    def __init__(self):
        self.cache_manager = cache_manager
    
    async def get_dashboard_data(self) -> Optional[dict]:
        """Get cached dashboard data"""
        return await self.cache_manager.get("dashboard_data")
    
    async def set_dashboard_data(self, data: dict, ttl: int = 60):
        """Cache dashboard data"""
        await self.cache_manager.set("dashboard_data", data, ttl)
    
    async def get_metric_history(self, metric_type: str) -> Optional[list]:
        """Get cached metric history"""
        return await self.cache_manager.get(f"metric_history:{metric_type}")
    
    async def set_metric_history(self, metric_type: str, history: list, ttl: int = 300):
        """Cache metric history"""
        await self.cache_manager.set(f"metric_history:{metric_type}", history, ttl)
    
    async def invalidate_dashboard(self):
        """Invalidate dashboard cache"""
        await self.cache_manager.delete("dashboard_data")
    
    async def invalidate_metric(self, metric_type: str):
        """Invalidate specific metric cache"""
        await self.cache_manager.delete(f"metric_history:{metric_type}")

# Global metrics cache instance
metrics_cache = MetricsCache()
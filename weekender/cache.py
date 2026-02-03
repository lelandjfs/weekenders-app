"""
Redis Cache for Weekender
==========================

Caches API responses to avoid redundant calls and failures.
TTL: 3 days
"""

import json
import redis
import hashlib
from typing import Any, Optional
from datetime import timedelta

# Redis connection
_redis_client = None

CACHE_TTL = timedelta(days=3)


def get_redis() -> redis.Redis:
    """Get Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        # Test connection
        try:
            _redis_client.ping()
            print("   [Cache] Redis connected")
        except redis.ConnectionError:
            print("   [Cache] Redis not available - caching disabled")
            _redis_client = None
    return _redis_client


def _make_key(prefix: str, city: str, start_date: str = None, end_date: str = None) -> str:
    """Create a cache key."""
    parts = [prefix, city.lower().strip()]
    if start_date:
        parts.append(start_date)
    if end_date:
        parts.append(end_date)
    key_str = ":".join(parts)
    return f"weekender:{key_str}"


def get_cached(prefix: str, city: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
    """Get cached data if available."""
    client = get_redis()
    if not client:
        return None

    key = _make_key(prefix, city, start_date, end_date)
    try:
        data = client.get(key)
        if data:
            print(f"   [Cache] HIT: {prefix} for {city}")
            return json.loads(data)
    except Exception as e:
        print(f"   [Cache] Error reading: {e}")
    return None


def set_cached(prefix: str, city: str, data: Any, start_date: str = None, end_date: str = None) -> bool:
    """Cache data with TTL."""
    client = get_redis()
    if not client:
        return False

    key = _make_key(prefix, city, start_date, end_date)
    try:
        client.setex(key, CACHE_TTL, json.dumps(data))
        print(f"   [Cache] SET: {prefix} for {city}")
        return True
    except Exception as e:
        print(f"   [Cache] Error writing: {e}")
        return False


def clear_cache(city: str = None) -> int:
    """Clear cache entries. If city provided, only clear that city."""
    client = get_redis()
    if not client:
        return 0

    try:
        if city:
            pattern = f"weekender:*:{city.lower()}:*"
        else:
            pattern = "weekender:*"

        keys = list(client.scan_iter(pattern))
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        print(f"   [Cache] Error clearing: {e}")
        return 0

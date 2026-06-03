import json
from typing import Any

import redis.asyncio as aioredis

from src.conf.config import settings


_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return a shared async Redis client, creating it on first call."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


def user_cache_key(username: str) -> str:
    """Return the Redis cache key for a given username."""
    return f"user:{username}"


async def cache_set(key: str, value: Any, ttl: int) -> None:
    """Serialize *value* to JSON and store it in Redis with the given TTL."""
    client = await get_redis()
    await client.set(key, json.dumps(value), ex=ttl)


async def cache_get(key: str) -> Any | None:
    """Retrieve and deserialize a JSON value from Redis, or return None on miss."""
    client = await get_redis()
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_delete(key: str) -> None:
    """Delete a key from Redis."""
    client = await get_redis()
    await client.delete(key)

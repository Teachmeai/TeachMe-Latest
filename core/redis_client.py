import asyncio
from typing import Optional

import redis.asyncio as aioredis

from core.config import config

_redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    global _redis_client
    if _redis_client is None:
        url = config.redis.URL or "redis://localhost:6379/0"
        _redis_client = aioredis.from_url(url, decode_responses=True)


def get_redis() -> aioredis.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client



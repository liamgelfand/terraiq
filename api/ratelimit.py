"""
Sliding-window rate limiter backed by Redis.

Each API key gets a sorted-set in Redis keyed by the key's ID.
Members are request timestamps (epoch seconds as score + unique suffix as member).
We count members in the rolling window and reject if over the limit.
"""
from __future__ import annotations

import time
import uuid

import redis.asyncio as aioredis
from fastapi import HTTPException

from api.config import settings

# One shared async Redis client (created lazily, shared across requests)
_redis: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


# Default policy: 60 requests per 60-second window per API key
_WINDOW_SECONDS = 60
_MAX_REQUESTS = 60


async def check_rate_limit(key_id: str, *, window: int = _WINDOW_SECONDS, limit: int = _MAX_REQUESTS) -> None:
    """
    Raise HTTP 429 if the given API key has exceeded `limit` requests in the
    last `window` seconds. Otherwise, record this request.
    """
    redis = _get_redis()
    now = time.time()
    rkey = f"rl:{key_id}"

    pipe = redis.pipeline()
    # Remove timestamps outside the window
    pipe.zremrangebyscore(rkey, "-inf", now - window)
    # Count remaining
    pipe.zcard(rkey)
    # Add this request
    pipe.zadd(rkey, {f"{now}:{uuid.uuid4().hex}": now})
    # Expire the key slightly longer than the window so Redis cleans up
    pipe.expire(rkey, window + 10)
    results = await pipe.execute()

    count_after_trim = results[1]  # zcard result (before adding current)
    if count_after_trim >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} requests per {window}s. Retry after {window}s.",
            headers={"Retry-After": str(window)},
        )

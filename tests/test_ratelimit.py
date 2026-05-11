"""
Unit tests for the sliding-window rate limiter.

Uses a fakeredis backend so no real Redis instance is required.
"""
from __future__ import annotations

import pytest
import fakeredis.aioredis as fakeredis
from fastapi import HTTPException

import api.ratelimit as ratelimit_module


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch):
    """Replace the real Redis client with an in-memory fakeredis instance."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(ratelimit_module, "_redis", fake)
    yield fake


async def test_first_request_passes():
    await ratelimit_module.check_rate_limit("key-1", window=60, limit=5)


async def test_requests_under_limit_all_pass():
    for _ in range(5):
        await ratelimit_module.check_rate_limit("key-2", window=60, limit=5)


async def test_request_over_limit_raises_429():
    for _ in range(5):
        await ratelimit_module.check_rate_limit("key-3", window=60, limit=5)
    with pytest.raises(HTTPException) as exc_info:
        await ratelimit_module.check_rate_limit("key-3", window=60, limit=5)
    assert exc_info.value.status_code == 429


async def test_different_keys_are_independent():
    """Exhausting the limit for one key must not affect another key."""
    for _ in range(5):
        await ratelimit_module.check_rate_limit("key-a", window=60, limit=5)
    # key-b has not been used — should still pass
    await ratelimit_module.check_rate_limit("key-b", window=60, limit=5)

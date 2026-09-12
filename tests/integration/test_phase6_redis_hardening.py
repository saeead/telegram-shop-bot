import os

import pytest
from redis.asyncio import Redis

from app.infrastructure.rate_limit import RedisRateLimiter
from app.infrastructure.redis_lock import RedisOwnedLock


@pytest.mark.asyncio
async def test_owned_lock_does_not_release_another_owner() -> None:
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("REDIS_URL is not configured")
    client = Redis.from_url(url, decode_responses=True)
    lock = RedisOwnedLock(client)
    key = "test:phase6:owned-lock"
    await client.delete(key)
    first = await lock.acquire(key, ttl_seconds=30)
    assert first is not None
    assert await lock.acquire(key, ttl_seconds=30) is None
    assert await lock.release(key, "wrong-owner") is False
    assert await client.get(key) == first
    assert await lock.release(key, first) is True
    assert await client.get(key) is None
    await client.aclose()


@pytest.mark.asyncio
async def test_rate_limit_enforces_window() -> None:
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("REDIS_URL is not configured")
    client = Redis.from_url(url, decode_responses=True)
    limiter = RedisRateLimiter(client)
    key = "test:phase6:rate-limit"
    await client.delete(key)
    assert await limiter.allow(key, limit=2, window_seconds=30)
    assert await limiter.allow(key, limit=2, window_seconds=30)
    assert not await limiter.allow(key, limit=2, window_seconds=30)
    await client.delete(key)
    await client.aclose()

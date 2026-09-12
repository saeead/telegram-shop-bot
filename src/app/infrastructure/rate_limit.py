"""Atomic Redis-backed fixed-window rate limiting."""

from __future__ import annotations

from redis.asyncio import Redis
from redis.exceptions import RedisError


class RedisRateLimiter:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        try:
            count = await self._client.incr(key)
            if count == 1:
                await self._client.expire(key, window_seconds)
            return int(count) <= limit
        except RedisError as exc:
            raise RuntimeError("redis rate limiter failed") from exc

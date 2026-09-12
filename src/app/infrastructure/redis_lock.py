"""Owner-safe Redis distributed locks with compare-and-delete release."""

from __future__ import annotations

from uuid import uuid4

from redis.asyncio import Redis
from redis.exceptions import RedisError


_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


class RedisOwnedLock:
    def __init__(self, client: Redis) -> None:
        self._client = client
        self._release = client.register_script(_RELEASE_SCRIPT)

    async def acquire(self, key: str, *, ttl_seconds: int) -> str | None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        token = uuid4().hex
        try:
            acquired = await self._client.set(key, token, nx=True, ex=ttl_seconds)
        except RedisError as exc:
            raise RuntimeError("redis lock acquisition failed") from exc
        return token if acquired else None

    async def release(self, key: str, token: str) -> bool:
        if not token:
            return False
        try:
            result = await self._release(keys=[key], args=[token])
        except RedisError as exc:
            raise RuntimeError("redis lock release failed") from exc
        return bool(result)

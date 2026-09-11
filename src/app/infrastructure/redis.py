from typing import cast

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.application.ports.cache import CachePort


class RedisStore(CachePort):
    """Redis adapter for transient state, locks, cache and idempotency records."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        result = await self._client.get(key)
        return cast(str | None, result)

    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> None:
        await self._client.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def acquire_lock(self, key: str, *, ttl_seconds: int) -> bool:
        return bool(await self._client.set(key, "1", nx=True, ex=ttl_seconds))

    async def release_lock(self, key: str) -> None:
        await self._client.delete(key)

    async def close(self) -> None:
        await self._client.aclose()

    async def ping(self) -> bool:
        return bool(await self._client.ping())


def create_redis_store(redis_url: str) -> RedisStore:
    return RedisStore(Redis.from_url(redis_url, decode_responses=True))


async def check_redis_health(store: RedisStore) -> bool:
    try:
        return await store.ping()
    except RedisError:
        return False

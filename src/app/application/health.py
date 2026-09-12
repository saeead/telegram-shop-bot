"""Health checks with no business-side effects."""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.database import check_database_health
from app.infrastructure.redis import RedisStore, check_redis_health


@dataclass(frozen=True, slots=True)
class HealthStatus:
    application: bool
    postgres: bool
    redis: bool

    @property
    def healthy(self) -> bool:
        return self.application and self.postgres and self.redis


async def check_health(engine: object, redis: RedisStore) -> HealthStatus:
    postgres = await check_database_health(engine)  # type: ignore[arg-type]
    redis_ok = await check_redis_health(redis)
    return HealthStatus(application=True, postgres=postgres, redis=redis_ok)

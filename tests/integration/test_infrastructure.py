import os

import pytest

from app.config.settings import Settings
from app.infrastructure.database import check_database_health, create_engine
from app.infrastructure.redis import check_redis_health, create_redis_store


@pytest.mark.asyncio
async def test_postgresql_health() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not configured for integration tests")

    settings = Settings(telegram_bot_token="integration-test-token", database_url=url)
    engine = create_engine(settings.database_url)
    try:
        assert await check_database_health(engine)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_redis_health() -> None:
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("REDIS_URL is not configured for integration tests")

    settings = Settings(telegram_bot_token="integration-test-token", redis_url=url)
    store = create_redis_store(settings.redis_url)
    try:
        assert await check_redis_health(store)
    finally:
        await store.close()

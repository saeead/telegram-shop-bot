"""Infrastructure failure-mode checks for Redis/DB unavailability."""

from __future__ import annotations

import os

import pytest

from app.application.health import check_health
from app.infrastructure.database import check_database_health, create_engine
from app.infrastructure.redis import check_redis_health, create_redis_store


@pytest.mark.asyncio
async def test_database_health_fails_for_unreachable_host() -> None:
    engine = create_engine("postgresql+asyncpg://postgres:postgres@127.0.0.1:1/telegram_file_store")
    try:
        assert await check_database_health(engine) is False
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_redis_health_fails_for_unreachable_host() -> None:
    store = create_redis_store("redis://127.0.0.1:1/0")
    try:
        assert await check_redis_health(store) is False
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_aggregate_health_reports_dependency_failures() -> None:
    engine = create_engine("postgresql+asyncpg://postgres:postgres@127.0.0.1:1/telegram_file_store")
    store = create_redis_store("redis://127.0.0.1:1/0")
    try:
        status = await check_health(engine, store)
        assert status.application is True
        assert status.postgres is False
        assert status.redis is False
        assert status.healthy is False
    finally:
        await store.close()
        await engine.dispose()


@pytest.mark.asyncio
async def test_redis_lock_cleared_after_key_loss_simulates_restart() -> None:
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("REDIS_URL is not configured")
    store = create_redis_store(url)
    key = "test:phase6:restart-lock"
    await store.delete(key)
    assert await store.acquire_lock(key, ttl_seconds=30) is True
    # Simulate Redis restart / key eviction by deleting the lock key.
    await store.delete(key)
    assert await store.get(key) is None
    assert await store.acquire_lock(key, ttl_seconds=30) is True
    await store.release_lock(key)
    await store.close()

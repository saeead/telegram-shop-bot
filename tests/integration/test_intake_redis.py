import os
from uuid import uuid4

import pytest

from app.catalog.classification import IncomingFile, IncomingMediaKind
from app.config.settings import Settings
from app.infrastructure.redis import create_redis_store
from app.infrastructure.redis_intake_store import RedisIntakeStore


@pytest.mark.asyncio
async def test_redis_intake_batch_round_trip() -> None:
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("REDIS_URL is not configured for integration tests")

    settings = Settings(telegram_bot_token="integration-test-token", redis_url=url)
    store = create_redis_store(settings.redis_url)
    intake_store = RedisIntakeStore(store, ttl_seconds=60)
    intake_id = uuid4()
    files = [
        IncomingFile(
            telegram_file_id="file-1",
            telegram_message_id=1,
            telegram_chat_id=-100123,
            media_kind=IncomingMediaKind.PHOTO,
        )
    ]
    try:
        await intake_store.save_batch(intake_id, files)
        loaded = await intake_store.load_batch(intake_id)
        assert loaded == files
        await intake_store.delete_batch(intake_id)
        assert await intake_store.load_batch(intake_id) == []
    finally:
        await store.close()

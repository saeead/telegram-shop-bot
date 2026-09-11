"""Redis-backed transient Product Intake state."""

from __future__ import annotations

import json
from uuid import UUID

from app.application.ports.cache import CachePort
from app.catalog.classification import IncomingFile, IncomingMediaKind


class RedisIntakeStore:
    def __init__(self, cache: CachePort, ttl_seconds: int = 86400) -> None:
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    async def save_batch(self, intake_id: UUID, files: list[IncomingFile]) -> None:
        payload = [
            {
                "telegram_file_id": item.telegram_file_id,
                "telegram_message_id": item.telegram_message_id,
                "telegram_chat_id": item.telegram_chat_id,
                "media_kind": item.media_kind.value,
                "original_filename": item.original_filename,
                "mime_type": item.mime_type,
                "size": item.size,
            }
            for item in files
        ]
        await self._cache.set(
            f"intake:{intake_id}:batch",
            json.dumps(payload),
            ttl_seconds=self._ttl_seconds,
        )

    async def load_batch(self, intake_id: UUID) -> list[IncomingFile]:
        raw = await self._cache.get(f"intake:{intake_id}:batch")
        if raw is None:
            return []
        payload = json.loads(raw)
        return [
            IncomingFile(
                telegram_file_id=item["telegram_file_id"],
                telegram_message_id=item["telegram_message_id"],
                telegram_chat_id=item["telegram_chat_id"],
                media_kind=IncomingMediaKind(item["media_kind"]),
                original_filename=item["original_filename"],
                mime_type=item["mime_type"],
                size=item["size"],
            )
            for item in payload
        ]

    async def delete_batch(self, intake_id: UUID) -> None:
        await self._cache.delete(f"intake:{intake_id}:batch")

"""Ports isolating delivery orchestration from Telegram and persistence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.delivery.domain import DeliveryRecord


class DeliveryRepositoryPort(Protocol):
    async def get(self, order_id: UUID, file_id: UUID) -> DeliveryRecord | None: ...

    async def list_for_order(self, order_id: UUID) -> list[DeliveryRecord]: ...

    async def save(self, record: DeliveryRecord) -> None: ...

    async def commit(self) -> None: ...


class DeliverySourcePort(Protocol):
    """Resolves a source message from private Archive/Backup channels."""

    async def copy_to_customer(
        self,
        source_chat_id: int,
        source_message_id: int,
        customer_telegram_id: int,
    ) -> int: ...


class DeliveryLockPort(Protocol):
    async def acquire_lock(self, key: str, *, ttl_seconds: int) -> bool: ...

    async def release_lock(self, key: str) -> None: ...

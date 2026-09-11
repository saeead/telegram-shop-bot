"""Application boundaries for public Store publication and administration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.product import Product


@dataclass(frozen=True, slots=True)
class StorePublication:
    product_id: UUID
    channel_id: int
    media_message_ids: tuple[int, ...]
    cta_message_id: int | None


@dataclass(frozen=True, slots=True)
class AuditEntry:
    actor: int
    action: str
    entity: str
    entity_id: str
    timestamp: datetime
    metadata: dict[str, object]


class StorePublisherPort(Protocol):
    async def publish(self, product: Product, channel_id: int) -> StorePublication: ...

    async def ensure_published(self, product: Product, channel_id: int) -> StorePublication: ...


class StoreRepositoryPort(Protocol):
    async def list_categories(self) -> list[str]: ...

    async def list_tags(self) -> list[str]: ...

    async def list_published(
        self, category: str | None = None, tag: str | None = None
    ) -> list[Product]: ...

    async def get_publication(self, product_id: UUID) -> StorePublication | None: ...

    async def save_publication(self, publication: StorePublication) -> None: ...

    async def save_audit(self, entry: AuditEntry) -> None: ...

    async def commit(self) -> None: ...

    async def get(self, product_id: UUID) -> Product | None: ...

    async def update(self, product: Product) -> None: ...

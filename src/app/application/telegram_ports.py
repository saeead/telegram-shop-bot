"""Application ports for Telegram intake; no aiogram types leak into this layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.catalog.classification import IncomingFile


@dataclass(frozen=True, slots=True)
class AdminReview:
    product_code: str
    name: str
    category: str | None
    tags: tuple[str, ...]
    price: str
    currency: str
    preview_count: int
    main_file_count: int


class TelegramIntakePort(Protocol):
    async def send_review(self, admin_chat_id: int, review: AdminReview) -> None: ...

    async def send_message(self, admin_chat_id: int, text: str) -> None: ...


class ProductIntakeStore(Protocol):
    async def save_batch(self, intake_id: str, files: list[IncomingFile]) -> None: ...

    async def load_batch(self, intake_id: str) -> list[IncomingFile]: ...

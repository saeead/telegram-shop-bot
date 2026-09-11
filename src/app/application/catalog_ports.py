"""Application ports for Product persistence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.intake import ProductIntake
from app.domain.product import Product


class ProductRepository(Protocol):
    async def add(self, product: Product) -> None: ...

    async def get(self, product_id: UUID) -> Product | None: ...

    async def get_by_code(self, product_code: str) -> Product | None: ...

    async def save_intake(self, intake: ProductIntake, admin_chat_id: int | None = None) -> None: ...

    async def get_intake(self, intake_id: UUID) -> ProductIntake | None: ...

    async def commit(self) -> None: ...

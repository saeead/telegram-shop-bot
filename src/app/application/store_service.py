"""Application services for public Store navigation and Admin product actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.application.store_ports import AuditEntry, StorePublisherPort, StoreRepositoryPort
from app.domain.product import Category, ProductStatus, Tag


class AuthorizationError(PermissionError):
    """Raised when an actor is not an authorized administrator."""


@dataclass(frozen=True, slots=True)
class ProductEdit:
    name: str | None = None
    price: Decimal | None = None
    category: str | None = None
    tags: tuple[str, ...] | None = None


class AdminAuthorizer:
    def __init__(self, admin_ids: frozenset[int]) -> None:
        self._admin_ids = admin_ids

    def require_admin(self, actor: int) -> None:
        if actor not in self._admin_ids:
            raise AuthorizationError("administrator authorization required")


class StoreService:
    def __init__(
        self,
        repository: StoreRepositoryPort,
        publisher: StorePublisherPort,
        authorizer: AdminAuthorizer,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._authorizer = authorizer

    async def categories(self) -> list[str]:
        return await self._repository.list_categories()

    async def tags(self) -> list[str]:
        return await self._repository.list_tags()

    async def products(self, category: str | None = None, tag: str | None = None):
        return await self._repository.list_published(category=category, tag=tag)

    async def publish(self, actor: int, product_id: UUID, channel_id: int):
        self._authorizer.require_admin(actor)
        product = await self._require_product(product_id)
        if product.status not in {ProductStatus.READY, ProductStatus.HIDDEN, ProductStatus.PUBLISHED}:
            raise ValueError("product is not publishable")
        publication = await self._publisher.ensure_published(product, channel_id)
        await self._repository.save_publication(publication)
        await self._audit(actor, "publish", product.id, {"channel_id": channel_id})
        if product.status is not ProductStatus.PUBLISHED:
            product.mark_published()
            await self._repository.update(product)
        await self._repository.commit()
        return publication

    async def hide(self, actor: int, product_id: UUID) -> None:
        self._authorizer.require_admin(actor)
        product = await self._require_product(product_id)
        product.hide()
        await self._repository.update(product)
        await self._audit(actor, "hide", product.id, {})
        await self._repository.commit()

    async def edit(self, actor: int, product_id: UUID, changes: ProductEdit) -> None:
        self._authorizer.require_admin(actor)
        product = await self._require_product(product_id)
        if changes.name is not None:
            name = changes.name.strip()
            if not name:
                raise ValueError("product name is required")
            product.name = name
        if changes.price is not None:
            if changes.price < 0:
                raise ValueError("price must not be negative")
            product.price = changes.price
        if changes.category is not None:
            product.set_category(Category(changes.category))
        if changes.tags is not None:
            product.set_tags([Tag(tag) for tag in changes.tags if tag.strip()])
        product.validate()
        await self._repository.update(product)
        await self._audit(actor, "edit_product", product.id, {"fields": _changed_fields(changes)})
        await self._repository.commit()

    async def republish(self, actor: int, product_id: UUID, channel_id: int):
        self._authorizer.require_admin(actor)
        product = await self._require_product(product_id)
        if product.status is ProductStatus.HIDDEN:
            product.mark_published()
            await self._repository.update(product)
        publication = await self._publisher.ensure_published(product, channel_id)
        await self._repository.save_publication(publication)
        await self._audit(actor, "republish", product.id, {"channel_id": channel_id})
        await self._repository.commit()
        return publication

    async def details(self, actor: int, product_id: UUID):
        self._authorizer.require_admin(actor)
        return await self._require_product(product_id)

    async def _require_product(self, product_id: UUID):
        product = await self._repository.get(product_id)
        if product is None:
            raise ValueError("product not found")
        return product

    async def _audit(self, actor: int, action: str, entity_id: UUID, metadata: dict[str, object]) -> None:
        await self._repository.save_audit(
            AuditEntry(
                actor=actor,
                action=action,
                entity="product",
                entity_id=str(entity_id),
                timestamp=datetime.now(UTC),
                metadata=metadata,
            )
        )


def _changed_fields(changes: ProductEdit) -> dict[str, bool]:
    return {
        "name": changes.name is not None,
        "price": changes.price is not None,
        "category": changes.category is not None,
        "tags": changes.tags is not None,
    }

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.store_ports import StoreRepositoryPort
from app.domain.product import Product, ProductFile, ProductPreview, ProductStatus, StorePublication
from app.infrastructure.models import (
    ProductFileModel,
    ProductModel,
    ProductPreviewModel,
    StorePublicationModel,
)


class SqlAlchemyProductRepository(StoreRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_product(self, product_id: UUID) -> Product | None:
        model = await self._session.scalar(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        if model is None:
            return None
        return self._to_domain(model)

    async def list_public_products(self) -> list[Product]:
        result = await self._session.scalars(
            select(ProductModel).where(ProductModel.status == ProductStatus.PUBLISHED)
        )
        return [self._to_domain(model) for model in result]

    async def list_public_products_by_category(self, category_id: UUID) -> list[Product]:
        result = await self._session.scalars(
            select(ProductModel).where(
                ProductModel.status == ProductStatus.PUBLISHED,
                ProductModel.category_id == category_id,
            )
        )
        return [self._to_domain(model) for model in result]

    async def list_public_products_by_tag(self, tag_name: str) -> list[Product]:
        wanted = tag_name.strip().lower()
        products = await self.list_public_products()
        return [
            product
            for product in products
            if any(item.name.lower() == wanted for item in product.tags)
        ]

    async def get_publication(self, product_id: UUID) -> StorePublication | None:
        model = await self._session.scalar(
            select(StorePublicationModel).where(StorePublicationModel.product_id == product_id)
        )
        if model is None:
            return None
        return StorePublication(
            product_id=model.product_id,
            channel_id=model.channel_id,
            media_group_message_ids=list(model.media_group_message_ids),
            buy_message_id=model.buy_message_id,
        )

    async def save_publication(self, publication: StorePublication) -> None:
        model = await self._session.scalar(
            select(StorePublicationModel).where(
                StorePublicationModel.product_id == publication.product_id
            )
        )
        if model is None:
            model = StorePublicationModel(
                product_id=publication.product_id,
                channel_id=publication.channel_id,
                media_group_message_ids=publication.media_group_message_ids,
                buy_message_id=publication.buy_message_id,
            )
            self._session.add(model)
        else:
            model.channel_id = publication.channel_id
            model.media_group_message_ids = publication.media_group_message_ids
            model.buy_message_id = publication.buy_message_id
        await self._session.flush()

    async def update_product(
        self,
        product_id: UUID,
        *,
        name: str | None = None,
        price: int | None = None,
        category_id: UUID | None = None,
        tags: Sequence[str] | None = None,
        status: ProductStatus | None = None,
    ) -> Product | None:
        model = await self._session.scalar(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        if model is None:
            return None
        if name is not None:
            model.name = name
        if price is not None:
            model.price = price
        if category_id is not None:
            model.category_id = category_id
        if tags is not None:
            model.tags = list(tags)
        if status is not None:
            model.status = status
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: ProductModel) -> Product:
        files = [
            ProductFile(
                id=item.id,
                telegram_file_id=item.telegram_file_id,
                file_name=item.file_name,
                mime_type=item.mime_type,
                file_size=item.file_size,
            )
            for item in model.files
        ]
        previews = [
            ProductPreview(
                id=item.id,
                telegram_file_id=item.telegram_file_id,
                media_type=item.media_type,
                sort_order=item.sort_order,
            )
            for item in model.previews
        ]
        return Product(
            id=model.id,
            code=model.code,
            name=model.name,
            price=model.price,
            category_id=model.category_id,
            tags=model.tags,
            status=model.status,
            files=files,
            previews=previews,
        )

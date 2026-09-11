"""SQLAlchemy implementation of the catalog and Store repository ports."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.catalog_ports import ProductRepository
from app.application.store_ports import AuditEntry, StorePublication, StoreRepositoryPort
from app.domain.intake import ProductIntake, ProductIntakeState
from app.domain.product import (
    Category,
    Product,
    ProductFile,
    ProductFileRole,
    ProductFileType,
    ProductStatus,
    Tag,
)
from app.infrastructure.models import (
    AuditLogModel,
    ProductFileModel,
    ProductIntakeModel,
    ProductModel,
    StorePublicationModel,
)


class SqlAlchemyProductRepository(ProductRepository, StoreRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, product: Product) -> None:
        now = datetime.now(UTC)
        model = ProductModel(
            id=product.id,
            product_code=product.product_code,
            name=product.name,
            category=product.category.name if product.category else None,
            tags=[tag.name for tag in product.tags],
            price=product.price,
            currency=product.currency,
            status=product.status.value,
            description=product.description,
            created_at=now,
            updated_at=now,
        )
        model.files = [
            ProductFileModel(
                id=file.id,
                product_id=product.id,
                telegram_file_id=file.telegram_file_id,
                telegram_message_id=file.telegram_message_id,
                telegram_chat_id=file.telegram_chat_id,
                file_type=file.file_type.value,
                role=file.role.value,
                original_filename=file.original_filename,
                mime_type=file.mime_type,
                size=file.size,
                ordering=file.ordering,
            )
            for file in product.files
        ]
        self._session.add(model)

    async def update(self, product: Product) -> None:
        model = await self._session.get(ProductModel, product.id)
        if model is None:
            raise ValueError("product not found")
        model.name = product.name
        model.category = product.category.name if product.category else None
        model.tags = [tag.name for tag in product.tags]
        model.price = product.price
        model.currency = product.currency
        model.status = product.status.value
        model.description = product.description
        model.updated_at = datetime.now(UTC)

    async def get(self, product_id: UUID) -> Product | None:
        result = await self._session.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.files))
            .where(ProductModel.id == product_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_code(self, product_code: str) -> Product | None:
        result = await self._session.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.files))
            .where(ProductModel.product_code == product_code.strip().upper())
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save_intake(self, intake: ProductIntake, admin_chat_id: int | None = None) -> None:
        model = await self._session.get(ProductIntakeModel, intake.id)
        now = datetime.now(UTC)
        if model is None:
            self._session.add(
                ProductIntakeModel(
                    id=intake.id,
                    product_id=intake.product_id,
                    state=intake.state.value,
                    error_message=intake.error_message,
                    admin_chat_id=admin_chat_id,
                    intake_metadata={},
                    created_at=now,
                    updated_at=now,
                )
            )
            return
        model.product_id = intake.product_id
        model.state = intake.state.value
        model.error_message = intake.error_message
        model.updated_at = now
        if admin_chat_id is not None:
            model.admin_chat_id = admin_chat_id

    async def get_intake(self, intake_id: UUID) -> ProductIntake | None:
        model = await self._session.get(ProductIntakeModel, intake_id)
        if model is None:
            return None
        return ProductIntake(
            id=model.id,
            product_id=model.product_id,
            state=ProductIntakeState(model.state),
            error_message=model.error_message,
        )

    async def list_categories(self) -> list[str]:
        result = await self._session.scalars(
            select(ProductModel.category)
            .where(ProductModel.category.is_not(None))
            .distinct()
            .order_by(ProductModel.category)
        )
        return [category for category in result if category is not None]

    async def list_tags(self) -> list[str]:
        products = await self._session.scalars(select(ProductModel))
        return sorted({tag for product in products for tag in product.tags})

    async def list_published(
        self, category: str | None = None, tag: str | None = None
    ) -> list[Product]:
        statement = (
            select(ProductModel)
            .options(selectinload(ProductModel.files))
            .where(ProductModel.status == ProductStatus.PUBLISHED.value)
        )
        if category:
            statement = statement.where(ProductModel.category == category)
        result = await self._session.scalars(statement)
        products = [self._to_domain(model) for model in result]
        if tag:
            wanted = tag.strip().lower()
            products = [
                product
                for product in products
                if any(item.name.lower() == wanted for item in product.tags)
            ]
        return products

    async def get_publication(self, product_id: UUID) -> StorePublication | None:
        model = await self._session.scalar(
            select(StorePublicationModel).where(
                StorePublicationModel.product_id == product_id
            )
        )
        if model is None:
            return None
        return StorePublication(
            product_id=model.product_id,
            channel_id=model.channel_id,
            media_message_ids=tuple(model.media_message_ids),
            cta_message_id=model.cta_message_id,
        )

    async def save_publication(self, publication: StorePublication) -> None:
        model = await self._session.scalar(
            select(StorePublicationModel).where(
                StorePublicationModel.product_id == publication.product_id
            )
        )
        now = datetime.now(UTC)
        if model is None:
            self._session.add(
                StorePublicationModel(
                    id=uuid4(),
                    product_id=publication.product_id,
                    channel_id=publication.channel_id,
                    media_message_ids=list(publication.media_message_ids),
                    cta_message_id=publication.cta_message_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            return
        model.channel_id = publication.channel_id
        model.media_message_ids = list(publication.media_message_ids)
        model.cta_message_id = publication.cta_message_id
        model.updated_at = now

    async def save_audit(self, entry: AuditEntry) -> None:
        self._session.add(
            AuditLogModel(
                id=uuid4(),
                actor=entry.actor,
                action=entry.action,
                entity=entry.entity,
                entity_id=entry.entity_id,
                timestamp=entry.timestamp,
                metadata_json=entry.metadata,
            )
        )

    async def commit(self) -> None:
        await self._session.commit()

    @staticmethod
    def _to_domain(model: ProductModel) -> Product:
        files = [
            ProductFile(
                id=file.id,
                telegram_file_id=file.telegram_file_id,
                telegram_message_id=file.telegram_message_id,
                telegram_chat_id=file.telegram_chat_id,
                file_type=ProductFileType(file.file_type),
                role=ProductFileRole(file.role),
                original_filename=file.original_filename,
                mime_type=file.mime_type,
                size=file.size,
                ordering=file.ordering,
            )
            for file in model.files
        ]
        return Product(
            id=model.id,
            product_code=model.product_code,
            name=model.name,
            price=model.price,
            currency=model.currency,
            category=Category(model.category) if model.category else None,
            tags=[Tag(name) for name in model.tags],
            status=ProductStatus(model.status),
            description=model.description,
            files=files,
        )

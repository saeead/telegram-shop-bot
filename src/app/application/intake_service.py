"""Application orchestration for Product Intake."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.application.catalog_ports import ProductRepository
from app.application.ports.cache import CachePort
from app.application.telegram_ports import AdminReview
from app.catalog.classification import IncomingFile, classify_batch
from app.catalog.product_code import generate_product_code
from app.domain.intake import ProductIntake, ProductIntakeState
from app.domain.product import Category, Product, ProductFile, Tag


class PublicationError(RuntimeError):
    """Raised when the external publication boundary cannot publish a product."""


class ProductPublisherPort:
    async def publish(self, product: Product) -> None:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class ProductMetadata:
    name: str
    category: str
    price: Decimal
    currency: str = "IRR"
    tags: tuple[str, ...] = ()
    description: str | None = None


class ProductIntakeService:
    def __init__(
        self,
        repository: ProductRepository,
        cache: CachePort,
        publisher: ProductPublisherPort,
    ) -> None:
        self._repository = repository
        self._cache = cache
        self._publisher = publisher

    async def receive_batch(self, admin_chat_id: int, files: list[IncomingFile]) -> ProductIntake:
        classified = classify_batch(files)
        intake = ProductIntake()
        intake.transition_to(ProductIntakeState.CLASSIFYING)
        product_code = generate_product_code()
        product_files = [
            ProductFile(
                telegram_file_id=item.source.telegram_file_id,
                telegram_message_id=item.source.telegram_message_id,
                telegram_chat_id=item.source.telegram_chat_id,
                file_type=item.file_type,
                role=item.role,
                original_filename=item.source.original_filename,
                mime_type=item.source.mime_type,
                size=item.source.size,
                ordering=item.ordering,
            )
            for item in classified
        ]
        product = Product(
            product_code=product_code,
            name=f"Untitled {product_code}",
            price=Decimal(0),
            files=product_files,
        )
        intake.attach_product(product.id)
        intake.transition_to(ProductIntakeState.WAITING_FOR_METADATA)
        await self._repository.add(product)
        await self._repository.save_intake(intake, admin_chat_id)
        await self._cache.set(f"intake:{intake.id}:admin", str(admin_chat_id), ttl_seconds=86400)
        await self._repository.commit()
        return intake

    async def set_metadata(self, intake_id: UUID, metadata: ProductMetadata) -> AdminReview:
        intake = await self._require_intake(intake_id)
        if intake.state is not ProductIntakeState.WAITING_FOR_METADATA:
            raise ValueError("intake is not waiting for metadata")
        self._validate_metadata(metadata)
        if intake.product_id is None:
            raise ValueError("intake has no product")
        product = await self._require_product(intake.product_id)
        product.name = metadata.name.strip()
        product.price = metadata.price
        product.currency = metadata.currency.strip().upper()
        product.set_category(Category(metadata.category))
        product.set_tags([Tag(tag) for tag in metadata.tags])
        product.description = metadata.description.strip() if metadata.description else None
        product.validate()
        await self._repository.update(product)
        intake.transition_to(ProductIntakeState.WAITING_FOR_ADMIN_CONFIRMATION)
        await self._repository.save_intake(intake)
        await self._repository.commit()
        return self._review(product)

    async def confirm(self, intake_id: UUID) -> None:
        intake = await self._require_intake(intake_id)
        if intake.state is not ProductIntakeState.WAITING_FOR_ADMIN_CONFIRMATION:
            raise ValueError("intake is not waiting for confirmation")
        if intake.product_id is None:
            raise ValueError("intake has no product")
        product = await self._require_product(intake.product_id)
        product.mark_ready()
        await self._repository.update(product)
        intake.transition_to(ProductIntakeState.PUBLISHING)
        await self._repository.save_intake(intake)
        await self._repository.commit()
        try:
            await self._publisher.publish(product)
        except PublicationError as exc:
            intake.fail(f"publication failed: {exc}")
            await self._repository.save_intake(intake)
            await self._repository.commit()
            raise
        product.mark_published()
        await self._repository.update(product)
        intake.transition_to(ProductIntakeState.PUBLISHED)
        await self._repository.save_intake(intake)
        await self._repository.commit()

    async def cancel(self, intake_id: UUID) -> None:
        intake = await self._require_intake(intake_id)
        if intake.state in {ProductIntakeState.PUBLISHED, ProductIntakeState.FAILED, ProductIntakeState.CANCELLED}:
            raise ValueError("intake cannot be cancelled in its current state")
        intake.transition_to(ProductIntakeState.CANCELLED)
        await self._repository.save_intake(intake)
        await self._repository.commit()

    async def review(self, intake_id: UUID) -> AdminReview:
        intake = await self._require_intake(intake_id)
        if intake.product_id is None:
            raise ValueError("intake has no product")
        return self._review(await self._require_product(intake.product_id))

    async def _require_intake(self, intake_id: UUID) -> ProductIntake:
        intake = await self._repository.get_intake(intake_id)
        if intake is None:
            raise ValueError("intake not found")
        return intake

    async def _require_product(self, product_id: UUID) -> Product:
        product = await self._repository.get(product_id)
        if product is None:
            raise ValueError("product not found")
        return product

    @staticmethod
    def _validate_metadata(metadata: ProductMetadata) -> None:
        if not metadata.name.strip():
            raise ValueError("product name is required")
        if not metadata.category.strip():
            raise ValueError("category is required")
        if metadata.price < 0:
            raise ValueError("price must not be negative")
        currency = metadata.currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("currency must be a three-letter code")

    @staticmethod
    def _review(product: Product) -> AdminReview:
        return AdminReview(
            product_code=product.product_code,
            name=product.name,
            category=product.category.name if product.category else None,
            tags=tuple(tag.name for tag in product.tags),
            price=str(product.price),
            currency=product.currency,
            preview_count=len(product.previews),
            main_file_count=len(product.main_files),
        )

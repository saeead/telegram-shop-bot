from decimal import Decimal
from uuid import UUID

import pytest

from app.application.catalog_ports import ProductRepository
from app.application.intake_service import ProductIntakeService, ProductMetadata, PublicationError, ProductPublisherPort
from app.application.ports.cache import CachePort
from app.catalog.classification import IncomingFile, IncomingMediaKind
from app.domain.intake import ProductIntake, ProductIntakeState
from app.domain.product import Product


class FakeCache(CachePort):
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> None:
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def acquire_lock(self, key: str, *, ttl_seconds: int) -> bool:
        return True

    async def release_lock(self, key: str) -> None:
        return None


class FakeRepository(ProductRepository):
    def __init__(self) -> None:
        self.products: dict[UUID, Product] = {}
        self.intakes: dict[UUID, ProductIntake] = {}

    async def add(self, product: Product) -> None:
        self.products[product.id] = product

    async def update(self, product: Product) -> None:
        self.products[product.id] = product

    async def get(self, product_id: UUID) -> Product | None:
        return self.products.get(product_id)

    async def get_by_code(self, product_code: str) -> Product | None:
        return next((p for p in self.products.values() if p.product_code == product_code), None)

    async def save_intake(self, intake: ProductIntake, admin_chat_id: int | None = None) -> None:
        self.intakes[intake.id] = intake

    async def get_intake(self, intake_id: UUID) -> ProductIntake | None:
        return self.intakes.get(intake_id)

    async def commit(self) -> None:
        return None


class FakePublisher(ProductPublisherPort):
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.published: list[str] = []

    async def publish(self, product: Product) -> None:
        if self.fail:
            raise PublicationError("telegram unavailable")
        self.published.append(product.product_code)


def source(message_id: int, filename: str) -> IncomingFile:
    return IncomingFile(
        telegram_file_id=f"file-{message_id}",
        telegram_message_id=message_id,
        telegram_chat_id=-100123,
        media_kind=IncomingMediaKind.DOCUMENT,
        original_filename=filename,
        mime_type="application/octet-stream",
        size=100,
    )


@pytest.mark.asyncio
async def test_intake_full_flow() -> None:
    repository = FakeRepository()
    publisher = FakePublisher()
    service = ProductIntakeService(repository, FakeCache(), publisher)

    intake = await service.receive_batch(9001, [source(1, "preview.zip"), source(2, "model.stl")])
    assert intake.state is ProductIntakeState.WAITING_FOR_METADATA

    review = await service.set_metadata(
        intake.id,
        ProductMetadata("Dragon", "Figures", Decimal("250000"), tags=("stl",)),
    )
    assert review.name == "Dragon"
    assert review.main_file_count == 2

    await service.confirm(intake.id)
    assert repository.intakes[intake.id].state is ProductIntakeState.PUBLISHED
    assert len(publisher.published) == 1


@pytest.mark.asyncio
async def test_publication_failure_moves_intake_to_failed() -> None:
    repository = FakeRepository()
    service = ProductIntakeService(repository, FakeCache(), FakePublisher(fail=True))
    intake = await service.receive_batch(9001, [source(1, "model.stl")])
    await service.set_metadata(intake.id, ProductMetadata("Model", "Figures", Decimal("1")))

    with pytest.raises(PublicationError):
        await service.confirm(intake.id)

    assert repository.intakes[intake.id].state is ProductIntakeState.FAILED

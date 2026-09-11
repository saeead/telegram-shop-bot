from decimal import Decimal

import pytest

from app.application.store_ports import StorePublication
from app.application.store_service import (
    AdminAuthorizer,
    AuthorizationError,
    ProductEdit,
    StoreService,
)
from app.domain.product import (
    Category,
    Product,
    ProductFile,
    ProductFileRole,
    ProductFileType,
    ProductStatus,
    Tag,
)


class FakeRepository:
    def __init__(self, product: Product) -> None:
        self.product = product
        self.publication = None
        self.audit = []
        self.commits = 0

    async def list_categories(self):
        return ["Models"]

    async def list_tags(self):
        return ["dragon"]

    async def list_published(self, category=None, tag=None):
        if self.product.status is not ProductStatus.PUBLISHED:
            return []
        if category and self.product.category.name != category:
            return []
        if tag and tag not in {item.name for item in self.product.tags}:
            return []
        return [self.product]

    async def get_publication(self, product_id):
        return self.publication

    async def save_publication(self, publication):
        self.publication = publication

    async def save_audit(self, entry):
        self.audit.append(entry)

    async def commit(self):
        self.commits += 1

    async def get(self, product_id):
        return self.product if product_id == self.product.id else None

    async def update(self, product):
        self.product = product


class FakePublisher:
    def __init__(self) -> None:
        self.calls = 0

    async def publish(self, product, channel_id):
        return await self.ensure_published(product, channel_id)

    async def ensure_published(self, product, channel_id):
        self.calls += 1
        return StorePublication(product.id, channel_id, (10, 11), 12)


def make_product() -> Product:
    return Product(
        product_code="P-001",
        name="Dragon",
        price=Decimal(1000),
        category=Category("Models"),
        tags=[Tag("dragon")],
        files=[
            ProductFile(
                telegram_file_id="preview",
                telegram_message_id=1,
                telegram_chat_id=2,
                file_type=ProductFileType.IMAGE,
                role=ProductFileRole.PREVIEW,
                original_filename=None,
                mime_type="image/jpeg",
                size=10,
            ),
            ProductFile(
                telegram_file_id="main",
                telegram_message_id=2,
                telegram_chat_id=2,
                file_type=ProductFileType.ARCHIVE,
                role=ProductFileRole.MAIN,
                original_filename="model.zip",
                mime_type="application/zip",
                size=20,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_publish_is_idempotent_and_excludes_main_files_from_publication():
    product = make_product()
    product.mark_ready()
    repository = FakeRepository(product)
    publisher = FakePublisher()
    service = StoreService(repository, publisher, AdminAuthorizer(frozenset({42})))

    first = await service.publish(42, product.id, -100)
    second = await service.publish(42, product.id, -100)

    assert first == second
    assert publisher.calls == 1
    assert first.media_message_ids == (10, 11)
    assert repository.product.status is ProductStatus.PUBLISHED


@pytest.mark.asyncio
async def test_unauthorized_admin_action_is_rejected():
    product = make_product()
    repository = FakeRepository(product)
    service = StoreService(repository, FakePublisher(), AdminAuthorizer(frozenset({42})))

    with pytest.raises(AuthorizationError):
        await service.edit(99, product.id, ProductEdit(price=Decimal(2000)))


@pytest.mark.asyncio
async def test_edit_price_and_hide_create_audit_entries():
    product = make_product()
    product.mark_ready()
    product.mark_published()
    repository = FakeRepository(product)
    service = StoreService(repository, FakePublisher(), AdminAuthorizer(frozenset({42})))

    await service.edit(42, product.id, ProductEdit(price=Decimal(2500)))
    await service.hide(42, product.id)

    assert repository.product.price == Decimal(2500)
    assert repository.product.status is ProductStatus.HIDDEN
    assert [entry.action for entry in repository.audit] == ["edit_product", "hide"]

from decimal import Decimal
from uuid import UUID

import pytest

from app.delivery.domain import DeliveryRecord, DeliveryStatus
from app.delivery.service import DeliveryError, DeliveryService
from app.domain.order import Order, OrderItem, OrderStatus
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType, ProductStatus


class FakeCommerce:
    def __init__(self, order: Order) -> None:
        self.order = order

    async def get_order(self, order_id: UUID):
        return self.order if order_id == self.order.id else None

    async def list_orders_for_customer(self, customer_telegram_id: int):
        return [self.order] if customer_telegram_id == self.order.customer_telegram_id else []


class FakeProducts:
    def __init__(self, product: Product) -> None:
        self.product = product

    async def get(self, product_id: UUID):
        return self.product if product_id == self.product.id else None

    async def get_by_code(self, code: str):
        return self.product if code == self.product.product_code else None


class FakeDeliveryRepo:
    def __init__(self) -> None:
        self.records: dict[tuple[UUID, UUID], DeliveryRecord] = {}

    async def get(self, order_id: UUID, file_id: UUID):
        return self.records.get((order_id, file_id))

    async def list_for_order(self, order_id: UUID):
        return list(self.records.values())

    async def save(self, record: DeliveryRecord) -> None:
        self.records[(record.order_id, record.file_id)] = record

    async def commit(self) -> None:
        return None


class FakeSource:
    def __init__(self, failures: set[int] | None = None) -> None:
        self.failures = failures or set()
        self.calls: list[tuple[int, int, int]] = []
        self.next_message = 100

    async def copy_to_customer(
        self, source_chat_id: int, source_message_id: int, customer_telegram_id: int
    ) -> int:
        self.calls.append((source_chat_id, source_message_id, customer_telegram_id))
        if source_chat_id in self.failures:
            raise TimeoutError("telegram timeout")
        self.next_message += 1
        return self.next_message


class FakeLock:
    def __init__(self) -> None:
        self.held = False

    async def acquire_lock(self, key: str, *, ttl_seconds: int) -> bool:
        if self.held:
            return False
        self.held = True
        return True

    async def release_lock(self, key: str) -> None:
        self.held = False


def make_fixture() -> tuple[Product, Order, FakeDeliveryRepo, FakeSource, DeliveryService]:
    files = [
        ProductFile(
            "f1", 20, 900, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "a.stl", None, 10, 0
        ),
        ProductFile(
            "f2", 21, 900, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "b.zip", None, 20, 1
        ),
    ]
    product = Product(
        "P-001",
        "Test Product",
        Decimal(1000),
        "IRR",
        status=ProductStatus.PUBLISHED,
        files=files,
    )
    order = Order(
        777,
        "IRR",
        [OrderItem(product.id, product.name, product.price, product.currency)],
        idempotency_key="order-1",
    )
    order.mark_paid()
    repo = FakeDeliveryRepo()
    source = FakeSource()
    service = DeliveryService(
        FakeProducts(product), FakeCommerce(order), repo, source, FakeLock(), 900, 901
    )
    return product, order, repo, source, service


@pytest.mark.asyncio
async def test_delivers_all_main_files_in_deterministic_order() -> None:
    _, order, repo, source, service = make_fixture()
    summary = await service.deliver(order.id, order.customer_telegram_id)
    assert summary.status is DeliveryStatus.DELIVERED
    assert summary.delivered == 2
    assert [call[1] for call in source.calls] == [20, 21]
    assert all(record.status is DeliveryStatus.DELIVERED for record in repo.records.values())


@pytest.mark.asyncio
async def test_retry_does_not_duplicate_delivered_files() -> None:
    _, order, _, source, service = make_fixture()
    await service.deliver(order.id, order.customer_telegram_id)
    first_count = len(source.calls)
    summary = await service.retry(order.id, order.customer_telegram_id)
    assert summary.status is DeliveryStatus.DELIVERED
    assert len(source.calls) == first_count


@pytest.mark.asyncio
async def test_archive_failure_falls_back_to_backup() -> None:
    product, order, repo, source, service = make_fixture()
    source.failures = {900}
    summary = await service.deliver(order.id, order.customer_telegram_id)
    assert summary.status is DeliveryStatus.DELIVERED
    assert source.calls[0][:2] == (900, product.main_files[0].telegram_message_id)
    assert source.calls[1][:2] == (901, product.main_files[0].telegram_message_id)
    assert len(repo.records) == 2


@pytest.mark.asyncio
async def test_partial_failure_is_retryable() -> None:
    _, order, repo, source, service = make_fixture()
    source.failures = {900, 901}
    summary = await service.deliver(order.id, order.customer_telegram_id)
    assert summary.status is DeliveryStatus.FAILED
    assert summary.failed == 2
    source.failures.clear()
    summary = await service.retry(order.id, order.customer_telegram_id)
    assert summary.status is DeliveryStatus.DELIVERED
    assert summary.delivered == 2
    assert all(record.attempt_count == 2 for record in repo.records.values())


@pytest.mark.asyncio
async def test_customer_cannot_use_foreign_order() -> None:
    _, order, _, _, service = make_fixture()
    with pytest.raises(DeliveryError, match="does not belong"):
        await service.deliver(order.id, 778)


@pytest.mark.asyncio
async def test_unpaid_order_cannot_be_delivered() -> None:
    _, order, _, _, service = make_fixture()
    order.status = OrderStatus.PENDING_PAYMENT
    with pytest.raises(DeliveryError, match="not paid"):
        await service.deliver(order.id, order.customer_telegram_id)


@pytest.mark.asyncio
async def test_product_code_must_belong_to_paid_order() -> None:
    product, order, _, _, service = make_fixture()
    assert (
        await service.validate_product_code(
            product.product_code, order.id, order.customer_telegram_id
        )
        == product.id
    )
    with pytest.raises(DeliveryError, match="not part"):
        await service.validate_product_code("OTHER", order.id, order.customer_telegram_id)


@pytest.mark.asyncio
async def test_duplicate_delivery_request_is_locked() -> None:
    _, order, _, _, service = make_fixture()
    lock = service._lock
    assert lock is not None
    await lock.acquire_lock(f"delivery:order:{order.id}", ttl_seconds=300)
    with pytest.raises(DeliveryError, match="already processing"):
        await service.deliver(order.id, order.customer_telegram_id)
    await lock.release_lock(f"delivery:order:{order.id}")

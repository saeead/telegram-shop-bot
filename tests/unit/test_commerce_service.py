from decimal import Decimal
from uuid import UUID

import pytest

from app.application.commerce_ports import (
    PaymentRequest,
    PaymentRequestResult,
    PaymentVerificationRequest,
    PaymentVerificationResult,
)
from app.application.commerce_service import CommerceError, CommerceService
from app.domain.order import Order, Payment
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType, ProductStatus


class FakeProducts:
    def __init__(self, product: Product) -> None:
        self.product = product

    async def get(self, product_id: UUID):
        return self.product if product_id == self.product.id else None


class FakeCommerceRepository:
    def __init__(self) -> None:
        self.orders: dict[UUID, Order] = {}
        self.payments: dict[UUID, Payment] = {}
        self.commits = 0

    async def get_order(self, order_id):
        return self.orders.get(order_id)

    async def get_order_by_idempotency_key(self, key):
        return next((item for item in self.orders.values() if item.idempotency_key == key), None)

    async def save_order(self, order):
        self.orders[order.id] = order

    async def get_payment(self, payment_id):
        return self.payments.get(payment_id)

    async def get_payment_by_order(self, order_id):
        return next((item for item in self.payments.values() if item.order_id == order_id), None)

    async def get_payment_by_provider_reference(self, provider, reference):
        return next(
            (
                item
                for item in self.payments.values()
                if item.provider == provider and item.provider_reference == reference
            ),
            None,
        )

    async def save_payment(self, payment):
        self.payments[payment.id] = payment

    async def commit(self):
        self.commits += 1


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.create_calls = 0
        self.verify_calls = 0
        self.fail_create = False
        self.fail_verify = False

    async def create_payment(self, request: PaymentRequest):
        self.create_calls += 1
        if self.fail_create:
            raise TimeoutError("provider timeout")
        return PaymentRequestResult("fake", "AUTH-1", "https://pay.test/AUTH-1", {})

    async def verify_payment(self, request: PaymentVerificationRequest):
        self.verify_calls += 1
        if self.fail_verify:
            return PaymentVerificationResult("fake", False, None, False, {})
        return PaymentVerificationResult("fake", True, "REF-1", False, {})

    async def refund(self, payment):
        return "REFUND-1"


def make_product() -> Product:
    return Product(
        product_code="P-1",
        name="Dragon",
        price=Decimal(1000),
        currency="IRR",
        status=ProductStatus.PUBLISHED,
        files=[
            ProductFile(
                telegram_file_id="preview",
                telegram_message_id=1,
                telegram_chat_id=2,
                file_type=ProductFileType.IMAGE,
                role=ProductFileRole.PREVIEW,
                original_filename=None,
                mime_type="image/jpeg",
                size=1,
            ),
            ProductFile(
                telegram_file_id="main",
                telegram_message_id=2,
                telegram_chat_id=2,
                file_type=ProductFileType.ARCHIVE,
                role=ProductFileRole.MAIN,
                original_filename="dragon.zip",
                mime_type="application/zip",
                size=1,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_order_creation_is_idempotent_and_snapshots_price():
    product = make_product()
    repository = FakeCommerceRepository()
    service = CommerceService(FakeProducts(product), repository, {})
    first = await service.create_order(100, product.id, 1, "order-key")
    product.price = Decimal(2000)
    second = await service.create_order(100, product.id, 1, "order-key")
    assert first.id == second.id
    assert first.total_amount == Decimal(1000)
    assert second.total_amount == Decimal(1000)


@pytest.mark.asyncio
async def test_payment_creation_is_idempotent():
    product = make_product()
    provider = FakeProvider()
    repository = FakeCommerceRepository()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(100, product.id, 1, "payment-key")
    first = await service.create_payment(order.id, "fake", "https://shop.test/callback")
    second = await service.create_payment(order.id, "fake", "https://shop.test/callback")
    assert first.authority == second.authority == "AUTH-1"
    assert provider.create_calls == 1


@pytest.mark.asyncio
async def test_payment_success_and_replayed_callback():
    product = make_product()
    provider = FakeProvider()
    repository = FakeCommerceRepository()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(100, product.id, 1, "order-1")
    await service.create_payment(order.id, "fake", "https://shop.test/callback")
    assert await service.handle_callback(order.id, "fake", "AUTH-1", "OK") is True
    assert await service.handle_callback(order.id, "fake", "AUTH-1", "OK") is True
    assert provider.verify_calls == 1
    assert repository.orders[order.id].status.value == "paid"


@pytest.mark.asyncio
async def test_invalid_callback_and_amount_mismatch_are_rejected():
    product = make_product()
    provider = FakeProvider()
    repository = FakeCommerceRepository()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(100, product.id, 1, "order-2")
    await service.create_payment(order.id, "fake", "https://shop.test/callback")
    with pytest.raises(CommerceError, match="status"):
        await service.handle_callback(order.id, "fake", "AUTH-1", "MAYBE")
    payment = next(iter(repository.payments.values()))
    payment.amount = Decimal(999)
    with pytest.raises(CommerceError, match="amount"):
        await service.handle_callback(order.id, "fake", "AUTH-1", "OK")


@pytest.mark.asyncio
async def test_provider_timeout_marks_payment_failed():
    product = make_product()
    provider = FakeProvider()
    provider.fail_create = True
    repository = FakeCommerceRepository()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(100, product.id, 1, "order-3")
    with pytest.raises(TimeoutError):
        await service.create_payment(order.id, "fake", "https://shop.test/callback")
    assert repository.orders[order.id].status.value == "payment_failed"
    assert next(iter(repository.payments.values())).status.value == "failed"


@pytest.mark.asyncio
async def test_provider_retry_after_failed_verification_can_succeed():
    product = make_product()
    provider = FakeProvider()
    provider.fail_verify = True
    repository = FakeCommerceRepository()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(100, product.id, 1, "order-4")
    await service.create_payment(order.id, "fake", "https://shop.test/callback")
    assert await service.handle_callback(order.id, "fake", "AUTH-1", "OK") is False
    provider.fail_verify = False
    assert await service.handle_callback(order.id, "fake", "AUTH-1", "OK") is True
    assert provider.verify_calls == 2


@pytest.mark.asyncio
async def test_already_paid_order_does_not_verify_again():
    product = make_product()
    provider = FakeProvider()
    repository = FakeCommerceRepository()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(100, product.id, 1, "order-5")
    await service.create_payment(order.id, "fake", "https://shop.test/callback")
    await service.handle_callback(order.id, "fake", "AUTH-1", "OK")
    assert await service.handle_callback(order.id, "fake", "AUTH-1", "OK") is True
    assert provider.verify_calls == 1

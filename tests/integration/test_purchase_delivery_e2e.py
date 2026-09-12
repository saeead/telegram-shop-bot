from decimal import Decimal
from uuid import UUID

import pytest

from app.application.commerce_ports import PaymentRequestResult, PaymentVerificationResult
from app.application.commerce_service import CommerceService
from app.delivery.service import DeliveryService
from app.domain.order import Order
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType, ProductStatus


class FakeProductRepo:
    def __init__(self, product: Product) -> None:
        self.product = product

    async def get(self, product_id: UUID):
        return self.product if product_id == self.product.id else None

    async def get_by_code(self, code: str):
        return self.product if code == self.product.product_code else None


class FakeCommerceRepo:
    def __init__(self) -> None:
        self.orders: dict[UUID, Order] = {}
        self.payments = {}

    async def get_order(self, order_id: UUID):
        return self.orders.get(order_id)

    async def get_order_by_idempotency_key(self, key: str):
        return next(
            (order for order in self.orders.values() if order.idempotency_key == key), None
        )

    async def list_orders_for_customer(self, customer_telegram_id: int):
        return [
            order
            for order in self.orders.values()
            if order.customer_telegram_id == customer_telegram_id
        ]

    async def save_order(self, order: Order):
        self.orders[order.id] = order

    async def get_payment(self, payment_id: UUID):
        return self.payments.get(payment_id)

    async def get_payment_by_order(self, order_id: UUID):
        return next(
            (payment for payment in self.payments.values() if payment.order_id == order_id), None
        )

    async def get_payment_by_provider_reference(self, provider: str, reference: str):
        return next(
            (
                payment
                for payment in self.payments.values()
                if payment.provider == provider and payment.provider_reference == reference
            ),
            None,
        )

    async def save_payment(self, payment):
        self.payments[payment.id] = payment

    async def commit(self):
        return None


class FakeProvider:
    name = "fake"

    async def create_payment(self, request):
        return PaymentRequestResult("fake", "AUTH-E2E", "https://pay.test/AUTH-E2E", {})

    async def verify_payment(self, request):
        return PaymentVerificationResult("fake", True, "REF-E2E", False, {})

    async def refund(self, payment):
        return "REFUND-E2E"


class FakeDeliveryRepo:
    def __init__(self) -> None:
        self.records = {}

    async def get(self, order_id, file_id):
        return self.records.get((order_id, file_id))

    async def list_for_order(self, order_id):
        return [
            record
            for (saved_order_id, _), record in self.records.items()
            if saved_order_id == order_id
        ]

    async def save(self, record):
        self.records[(record.order_id, record.file_id)] = record

    async def commit(self):
        return None


class FakeSource:
    def __init__(self) -> None:
        self.sent: list[tuple[int, int, int]] = []
        self.counter = 500

    async def copy_to_customer(self, source_chat_id, source_message_id, customer_telegram_id):
        self.sent.append((source_chat_id, source_message_id, customer_telegram_id))
        self.counter += 1
        return self.counter


@pytest.mark.asyncio
async def test_admin_to_store_buy_payment_verify_delivery() -> None:
    product = Product(
        "E2E-001",
        "E2E Product",
        Decimal(2500),
        "IRR",
        status=ProductStatus.PUBLISHED,
        files=[
            ProductFile(
                "a", 101, 900, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "one.stl", None, 10, 0
            ),
            ProductFile(
                "b", 102, 900, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "two.zip", None, 20, 1
            ),
        ],
    )
    products = FakeProductRepo(product)
    commerce_repo = FakeCommerceRepo()
    commerce = CommerceService(products, commerce_repo, {"fake": FakeProvider()})

    order = await commerce.create_order(777, product.id, 1, "e2e-order-1")
    payment = await commerce.create_payment(order.id, "fake", "https://bot.test/callback")
    assert payment.authority == "AUTH-E2E"
    assert await commerce.handle_callback(order.id, "fake", "AUTH-E2E", "OK") is True

    source = FakeSource()
    delivery = DeliveryService(
        products,
        commerce_repo,
        FakeDeliveryRepo(),
        source,
        archive_channel_id=900,
        backup_channel_id=901,
    )
    summary = await delivery.deliver(order.id, 777)
    assert summary.delivered == 2
    assert summary.status.value == "delivered"
    assert [message_id for _, message_id, _ in source.sent] == [101, 102]

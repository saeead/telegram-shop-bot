from decimal import Decimal

import pytest
from aiohttp.test_utils import TestClient, TestServer

from app.application.commerce_ports import PaymentRequestResult, PaymentVerificationResult
from app.application.commerce_service import CommerceService
from app.delivery.domain import DeliveryStatus, DeliverySummary
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType, ProductStatus
from app.presentation.payment_webhook import create_payment_app


def _product() -> Product:
    return Product(
        product_code="WH-1",
        name="Widget",
        price=Decimal(5000),
        currency="IRR",
        status=ProductStatus.PUBLISHED,
        files=[
            ProductFile(
                "f1",
                11,
                200,
                ProductFileType.ARCHIVE,
                ProductFileRole.MAIN,
                "w.stl",
                None,
                5,
            )
        ],
    )


class FakeProducts:
    def __init__(self, product: Product) -> None:
        self.product = product

    async def get(self, product_id):
        return self.product if product_id == self.product.id else None

    async def get_by_code(self, code):
        return self.product


class FakeCommerceRepo:
    def __init__(self) -> None:
        self.orders: dict = {}
        self.payments: dict = {}

    async def get_order(self, order_id):
        return self.orders.get(order_id)

    async def get_order_by_idempotency_key(self, key):
        return None

    async def list_orders_for_customer(self, customer_telegram_id):
        return []

    async def save_order(self, order):
        self.orders[order.id] = order

    async def get_payment(self, payment_id):
        return self.payments.get(payment_id)

    async def get_payment_by_order(self, order_id):
        return next((p for p in self.payments.values() if p.order_id == order_id), None)

    async def get_payment_by_provider_reference(self, provider, reference):
        return None

    async def save_payment(self, payment):
        self.payments[payment.id] = payment

    async def commit(self):
        return None


class FakeProvider:
    name = "zarinpal"

    async def create_payment(self, request):
        return PaymentRequestResult("zarinpal", "AUTH", "https://pay", {})

    async def verify_payment(self, request):
        return PaymentVerificationResult("zarinpal", True, "REF", False, {})

    async def refund(self, payment):
        return "r"


class FakeDelivery:
    async def deliver(self, order_id, customer_telegram_id):
        return DeliverySummary(order_id, 1, 0, 0, DeliveryStatus.DELIVERED)


class SessionCM:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *args):
        return None


@pytest.mark.asyncio
async def test_zarinpal_callback_pays_and_delivers() -> None:
    product = _product()
    repo = FakeCommerceRepo()
    commerce = CommerceService(FakeProducts(product), repo, {"zarinpal": FakeProvider()})
    order = await commerce.create_order(99, product.id, 1, "wh-1")
    await commerce.create_payment(order.id, "zarinpal", "https://bot.test/callback")

    notes: list[tuple[int, str]] = []

    async def notify(cid: int, text: str) -> None:
        notes.append((cid, text))

    def session_factory():
        return SessionCM(object())

    def commerce_factory(_session):
        return commerce

    def delivery_factory(_session):
        return FakeDelivery()

    app = create_payment_app(
        session_factory, commerce_factory, delivery_factory, bot_notifier=notify
    )
    async with TestClient(TestServer(app)) as client:
        response = await client.get(
            "/payments/zarinpal/callback",
            params={"order_id": str(order.id), "Authority": "AUTH", "Status": "OK"},
        )
        assert response.status == 200
        assert await response.text() == "OK"
    assert notes and notes[0][0] == 99
    assert "Payment confirmed" in notes[0][1]

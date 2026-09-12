"""Verify commerce/delivery emit operational metrics at service boundaries."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.application.commerce_ports import PaymentRequestResult, PaymentVerificationResult
from app.application.commerce_service import CommerceService
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType, ProductStatus
from app.infrastructure.observability import clear_metrics, snapshot_metrics


class FakeProducts:
    def __init__(self, product: Product) -> None:
        self.product = product

    async def get(self, product_id):
        return self.product if product_id == self.product.id else None


class FakeRepo:
    def __init__(self) -> None:
        self.orders = {}
        self.payments = {}

    async def get_order(self, order_id):
        return self.orders.get(order_id)

    async def get_order_by_idempotency_key(self, key):
        return next((o for o in self.orders.values() if o.idempotency_key == key), None)

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
    name = "fake"

    async def create_payment(self, request):
        return PaymentRequestResult("fake", "AUTH", "https://pay", {})

    async def verify_payment(self, request):
        return PaymentVerificationResult("fake", True, "REF", False, {})

    async def refund(self, payment):
        return "r"


def _product() -> Product:
    return Product(
        "M-1",
        "Metric",
        Decimal(100),
        "IRR",
        status=ProductStatus.PUBLISHED,
        files=[
            ProductFile("f", 1, 2, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "a.zip", None, 1)
        ],
    )


@pytest.mark.asyncio
async def test_order_and_payment_metrics_increment() -> None:
    clear_metrics()
    product = _product()
    service = CommerceService(FakeProducts(product), FakeRepo(), {"fake": FakeProvider()})
    order = await service.create_order(1, product.id, 1, "metric-order")
    await service.create_payment(order.id, "fake", "https://cb")
    assert await service.handle_callback(order.id, "fake", "AUTH", "OK") is True
    metrics = snapshot_metrics()
    assert metrics.get("orders_total", 0) >= 1
    assert metrics.get("payments_total", 0) >= 1
    clear_metrics()

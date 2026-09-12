from decimal import Decimal

import pytest

from app.application.commerce_ports import PaymentRequestResult
from app.application.commerce_service import CommerceError, CommerceService
from app.domain.order import Order
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType, ProductStatus


def _published_product(code: str = "BUY-1") -> Product:
    return Product(
        product_code=code,
        name="Model",
        price=Decimal(1000),
        currency="IRR",
        status=ProductStatus.PUBLISHED,
        files=[
            ProductFile(
                "file-1",
                1,
                100,
                ProductFileType.ARCHIVE,
                ProductFileRole.MAIN,
                "a.stl",
                None,
                10,
            )
        ],
    )


class FakeProducts:
    def __init__(self, product: Product) -> None:
        self.product = product

    async def get(self, product_id):
        return self.product if product_id == self.product.id else None


class FakeCommerceRepo:
    def __init__(self) -> None:
        self.orders: dict = {}
        self.payments: dict = {}

    async def get_order(self, order_id):
        return self.orders.get(order_id)

    async def get_order_by_idempotency_key(self, key):
        return next((o for o in self.orders.values() if o.idempotency_key == key), None)

    async def list_orders_for_customer(self, customer_telegram_id):
        return [o for o in self.orders.values() if o.customer_telegram_id == customer_telegram_id]

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
        return PaymentRequestResult(
            provider="zarinpal",
            authority="AUTH-1",
            payment_url="https://pay.test/AUTH-1",
            raw_metadata={},
        )

    async def verify_payment(self, request):
        raise NotImplementedError

    async def refund(self, payment):
        return "x"


@pytest.mark.asyncio
async def test_buy_creates_order_and_payment_link() -> None:
    product = _published_product()
    commerce = CommerceService(
        FakeProducts(product), FakeCommerceRepo(), {"zarinpal": FakeProvider()}
    )
    order = await commerce.create_order(42, product.id, 1, f"buy:42:{product.id}")
    payment = await commerce.create_payment(order.id, "zarinpal", "https://bot.test/callback")
    assert isinstance(order, Order)
    assert payment.payment_url.startswith("https://pay.test/")


@pytest.mark.asyncio
async def test_buy_rejects_unpublished_product() -> None:
    product = _published_product("BUY-2")
    product.status = ProductStatus.READY
    commerce = CommerceService(
        FakeProducts(product), FakeCommerceRepo(), {"zarinpal": FakeProvider()}
    )
    with pytest.raises(CommerceError):
        await commerce.create_order(42, product.id, 1, "k")

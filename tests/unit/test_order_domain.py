from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.order import Order, OrderItem, OrderStatus, Payment


def make_order() -> Order:
    return Order(
        customer_telegram_id=123,
        currency="IRR",
        items=[
            OrderItem(
                product_id=uuid4(),
                product_name="Dragon",
                unit_price=Decimal(1000),
                currency="IRR",
            )
        ],
        idempotency_key="order-key-1",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )


def test_order_snapshots_price_and_total():
    order = make_order()
    assert order.total_amount == Decimal(1000)
    order.items[0] = OrderItem(
        product_id=order.items[0].product_id,
        product_name=order.items[0].product_name,
        unit_price=Decimal(2000),
        currency="IRR",
    )
    assert order.total_amount == Decimal(2000)


def test_payment_cannot_start_for_wrong_amount():
    order = make_order()
    payment = Payment(order.id, "fake", Decimal(999), "IRR")
    with pytest.raises(ValueError, match="amount"):
        order.start_payment(payment)


def test_expired_order_cannot_be_paid():
    order = Order(
        customer_telegram_id=123,
        currency="IRR",
        items=[
            OrderItem(uuid4(), "Dragon", Decimal(1000), "IRR"),
        ],
        idempotency_key="expired-key",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="expired"):
        order.start_payment(Payment(order.id, "fake", Decimal(1000), "IRR"))
    assert order.status is OrderStatus.EXPIRED

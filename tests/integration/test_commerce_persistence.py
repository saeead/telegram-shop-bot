import os
from decimal import Decimal
from uuid import uuid4

import pytest

from app.config.settings import Settings
from app.domain.order import Order, OrderItem, Payment, PaymentAttempt, PaymentAttemptStatus
from app.infrastructure.commerce_repository import SqlAlchemyCommerceRepository
from app.infrastructure.database import create_engine, create_session_factory


@pytest.mark.asyncio
async def test_order_payment_attempt_round_trip() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not configured for integration tests")
    settings = Settings(telegram_bot_token="integration-test-token", database_url=url)
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    order = Order(
        customer_telegram_id=777,
        currency="IRR",
        items=[OrderItem(uuid4(), "Integration Product", Decimal(1200), "IRR")],
        idempotency_key=f"integration-{uuid4()}",
    )
    payment = Payment(order.id, "fake", order.total_amount, order.currency)
    payment.attempts.append(
        PaymentAttempt(
            provider="fake",
            amount=order.total_amount,
            currency=order.currency,
            status=PaymentAttemptStatus.REDIRECTED,
            provider_reference="AUTH-INTEGRATION",
            idempotency_key=f"attempt-{uuid4()}",
            metadata={"payment_url": "https://example.test/pay"},
        )
    )
    payment.provider_reference = "AUTH-INTEGRATION"
    try:
        async with session_factory() as session:
            repository = SqlAlchemyCommerceRepository(session)
            await repository.save_order(order)
            await repository.save_payment(payment)
            await repository.commit()
            loaded_order = await repository.get_order(order.id)
            loaded_payment = await repository.get_payment_by_order(order.id)
            assert loaded_order is not None
            assert loaded_order.total_amount == Decimal(1200)
            assert loaded_order.items[0].unit_price == Decimal(1200)
            assert loaded_payment is not None
            assert loaded_payment.provider_reference == "AUTH-INTEGRATION"
            assert loaded_payment.attempts[0].metadata["payment_url"] == "https://example.test/pay"
            model = await session.get(type(repository._session.get), None) if False else None
            del model
            await session.delete(await session.get(type(loaded_order), loaded_order.id) if False else None) if False else None
            await session.execute(__import__("sqlalchemy").text("DELETE FROM orders WHERE id = :id"), {"id": order.id})
            await session.commit()
    finally:
        await engine.dispose()

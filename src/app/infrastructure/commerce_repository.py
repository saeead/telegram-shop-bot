"""SQLAlchemy persistence implementation for orders and payments."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.commerce_ports import CommerceRepositoryPort
from app.domain.order import Order, OrderItem, OrderStatus, Payment, PaymentAttempt, PaymentAttemptStatus, PaymentStatus
from app.infrastructure.models import OrderItemModel, OrderModel, PaymentAttemptModel, PaymentModel


class SqlAlchemyCommerceRepository(CommerceRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_order(self, order_id: UUID) -> Order | None:
        model = await self._session.scalar(
            select(OrderModel)
            .options(
                selectinload(OrderModel.items),
                selectinload(OrderModel.payments).selectinload(PaymentModel.attempts),
            )
            .where(OrderModel.id == order_id)
        )
        return self._order_to_domain(model) if model else None

    async def get_order_by_idempotency_key(self, key: str) -> Order | None:
        model = await self._session.scalar(
            select(OrderModel)
            .options(
                selectinload(OrderModel.items),
                selectinload(OrderModel.payments).selectinload(PaymentModel.attempts),
            )
            .where(OrderModel.idempotency_key == key)
        )
        return self._order_to_domain(model) if model else None

    async def list_orders_for_customer(self, customer_telegram_id: int) -> list[Order]:
        result = await self._session.scalars(
            select(OrderModel)
            .options(
                selectinload(OrderModel.items),
                selectinload(OrderModel.payments).selectinload(PaymentModel.attempts),
            )
            .where(OrderModel.customer_telegram_id == customer_telegram_id)
            .order_by(OrderModel.created_at.desc())
        )
        return [self._order_to_domain(model) for model in result]

    async def save_order(self, order: Order) -> None:
        model = await self._session.get(OrderModel, order.id)
        if model is None:
            model = OrderModel(
                id=order.id,
                order_code=order.order_code,
                customer_telegram_id=order.customer_telegram_id,
                currency=order.currency,
                total_amount=order.total_amount,
                status=order.status.value,
                idempotency_key=order.idempotency_key,
                expires_at=order.expires_at,
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
            model.items = [
                OrderItemModel(
                    id=item.id,
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    unit_price=item.unit_price,
                    currency=item.currency,
                    quantity=item.quantity,
                )
                for item in order.items
            ]
            self._session.add(model)
            return
        model.status = order.status.value
        model.total_amount = order.total_amount
        model.expires_at = order.expires_at
        model.updated_at = order.updated_at

    async def get_payment(self, payment_id: UUID) -> Payment | None:
        model = await self._session.scalar(
            select(PaymentModel)
            .options(selectinload(PaymentModel.attempts))
            .where(PaymentModel.id == payment_id)
        )
        return self._payment_to_domain(model) if model else None

    async def get_payment_by_order(self, order_id: UUID) -> Payment | None:
        model = await self._session.scalar(
            select(PaymentModel)
            .options(selectinload(PaymentModel.attempts))
            .where(PaymentModel.order_id == order_id)
        )
        return self._payment_to_domain(model) if model else None

    async def get_payment_by_provider_reference(self, provider: str, reference: str) -> Payment | None:
        model = await self._session.scalar(
            select(PaymentModel)
            .options(selectinload(PaymentModel.attempts))
            .where(PaymentModel.provider == provider, PaymentModel.provider_reference == reference)
        )
        return self._payment_to_domain(model) if model else None

    async def save_payment(self, payment: Payment) -> None:
        model = await self._session.scalar(
            select(PaymentModel)
            .options(selectinload(PaymentModel.attempts))
            .where(PaymentModel.id == payment.id)
        )
        if model is None:
            model = PaymentModel(
                id=payment.id,
                order_id=payment.order_id,
                provider=payment.provider,
                amount=payment.amount,
                currency=payment.currency,
                status=payment.status.value,
                provider_reference=payment.provider_reference,
                created_at=payment.created_at,
                verified_at=payment.verified_at,
            )
            self._session.add(model)
        else:
            model.status = payment.status.value
            model.provider_reference = payment.provider_reference
            model.verified_at = payment.verified_at
        existing = {attempt.id for attempt in model.attempts}
        for attempt in payment.attempts:
            if attempt.id in existing:
                continue
            model.attempts.append(
                PaymentAttemptModel(
                    id=attempt.id,
                    payment_id=payment.id,
                    provider=attempt.provider,
                    provider_reference=attempt.provider_reference,
                    amount=attempt.amount,
                    currency=attempt.currency,
                    status=attempt.status.value,
                    idempotency_key=attempt.idempotency_key,
                    metadata_json=dict(attempt.metadata),
                    created_at=attempt.created_at,
                    verified_at=attempt.verified_at,
                )
            )

    async def commit(self) -> None:
        await self._session.commit()

    @staticmethod
    def _order_to_domain(model: OrderModel) -> Order:
        return Order(
            id=model.id,
            order_code=model.order_code,
            customer_telegram_id=model.customer_telegram_id,
            currency=model.currency,
            items=[
                OrderItem(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    unit_price=Decimal(item.unit_price),
                    currency=item.currency,
                    quantity=item.quantity,
                )
                for item in model.items
            ],
            status=OrderStatus(model.status),
            expires_at=model.expires_at,
            idempotency_key=model.idempotency_key,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _payment_to_domain(model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            order_id=model.order_id,
            provider=model.provider,
            amount=Decimal(model.amount),
            currency=model.currency,
            status=PaymentStatus(model.status),
            provider_reference=model.provider_reference,
            created_at=model.created_at,
            verified_at=model.verified_at,
            attempts=[
                PaymentAttempt(
                    id=attempt.id,
                    provider=attempt.provider,
                    amount=Decimal(attempt.amount),
                    currency=attempt.currency,
                    status=PaymentAttemptStatus(attempt.status),
                    provider_reference=attempt.provider_reference,
                    idempotency_key=attempt.idempotency_key,
                    metadata=dict(attempt.metadata_json),
                    created_at=attempt.created_at,
                    verified_at=attempt.verified_at,
                )
                for attempt in model.attempts
            ],
        )

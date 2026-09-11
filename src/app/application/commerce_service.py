"""Use-case orchestration for order creation and payment verification."""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from app.application.catalog_ports import ProductRepository
from app.application.commerce_ports import (
    CommerceRepositoryPort,
    PaymentProvider,
    PaymentRequest,
    PaymentRequestResult,
    PaymentVerificationRequest,
)
from app.domain.order import (
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
)


class CommerceError(ValueError):
    """Expected commerce validation failure."""


class CommerceService:
    def __init__(
        self,
        products: ProductRepository,
        repository: CommerceRepositoryPort,
        providers: dict[str, PaymentProvider],
    ) -> None:
        self._products = products
        self._repository = repository
        self._providers = providers

    async def create_order(
        self,
        customer_telegram_id: int,
        product_id: UUID,
        quantity: int,
        idempotency_key: str,
        expires_at: datetime | None = None,
    ) -> Order:
        existing = await self._repository.get_order_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing
        product = await self._products.get(product_id)
        if product is None or product.status.value != "published":
            raise CommerceError("product is not available for purchase")
        if quantity <= 0:
            raise CommerceError("quantity must be positive")
        order = Order(
            customer_telegram_id=customer_telegram_id,
            currency=product.currency,
            items=[
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    currency=product.currency,
                    quantity=quantity,
                )
            ],
            idempotency_key=idempotency_key,
            expires_at=expires_at,
        )
        await self._repository.save_order(order)
        await self._repository.commit()
        return order

    async def create_payment(
        self,
        order_id: UUID,
        provider_name: str,
        callback_url: str,
    ) -> PaymentRequestResult:
        order = await self._require_order(order_id)
        if order.is_expired():
            order.expire()
            await self._repository.save_order(order)
            await self._repository.commit()
            raise CommerceError("order is not payable")
        if order.status is OrderStatus.PAID:
            raise CommerceError("order is already paid")
        if order.status in {OrderStatus.CANCELLED, OrderStatus.EXPIRED}:
            raise CommerceError("order is not payable")
        provider = self._provider(provider_name)
        payment = await self._repository.get_payment_by_order(order.id)
        if payment is None:
            payment = Payment(
                order_id=order.id,
                provider=provider.name,
                amount=order.total_amount,
                currency=order.currency,
            )
            await self._repository.save_payment(payment)
        elif payment.provider != provider.name:
            raise CommerceError("order already has a different payment provider")
        elif payment.status is PaymentStatus.SUCCEEDED:
            raise CommerceError("order is already paid")

        if payment.attempts and payment.attempts[-1].provider_reference:
            attempt = payment.attempts[-1]
            return PaymentRequestResult(
                provider=payment.provider,
                authority=attempt.provider_reference or "",
                payment_url=attempt.metadata.get("payment_url", "")
                if isinstance(attempt.metadata.get("payment_url", ""), str)
                else "",
                raw_metadata=dict(attempt.metadata),
            )

        order.start_payment(payment)
        await self._repository.save_order(order)
        payment.mark_processing()
        attempt = PaymentAttempt(
            provider=provider.name,
            amount=payment.amount,
            currency=payment.currency,
            idempotency_key=f"{order.id}:{provider.name}:{len(payment.attempts) + 1}",
        )
        payment.attempts.append(attempt)
        await self._repository.save_payment(payment)
        try:
            result = await provider.create_payment(
                PaymentRequest(
                    payment_id=payment.id,
                    order_id=order.id,
                    amount=payment.amount,
                    currency=payment.currency,
                    description=f"Order {order.order_code}",
                    callback_url=self._callback_url(callback_url, order.id),
                    idempotency_key=attempt.idempotency_key,
                )
            )
        except TimeoutError:
            payment.attempts[-1] = PaymentAttempt(
                provider=attempt.provider,
                amount=attempt.amount,
                currency=attempt.currency,
                status=PaymentAttemptStatus.TIMEOUT,
                idempotency_key=attempt.idempotency_key,
                metadata={"error": "provider_timeout"},
            )
            payment.mark_failed()
            order.mark_payment_failed()
            await self._repository.save_payment(payment)
            await self._repository.save_order(order)
            await self._repository.commit()
            raise
        except Exception:
            payment.attempts[-1] = PaymentAttempt(
                provider=attempt.provider,
                amount=attempt.amount,
                currency=attempt.currency,
                status=PaymentAttemptStatus.FAILED,
                idempotency_key=attempt.idempotency_key,
                metadata={"error": "provider_error"},
            )
            payment.mark_failed()
            order.mark_payment_failed()
            await self._repository.save_payment(payment)
            await self._repository.save_order(order)
            await self._repository.commit()
            raise

        payment.attempts[-1] = PaymentAttempt(
            provider=attempt.provider,
            amount=attempt.amount,
            currency=attempt.currency,
            status=PaymentAttemptStatus.REDIRECTED,
            provider_reference=result.authority,
            idempotency_key=attempt.idempotency_key,
            metadata=dict(result.raw_metadata) | {"payment_url": result.payment_url},
            created_at=attempt.created_at,
        )
        payment.provider_reference = result.authority
        await self._repository.save_payment(payment)
        await self._repository.commit()
        return result

    async def handle_callback(
        self,
        order_id: UUID,
        provider_name: str,
        authority: str,
        status: str,
    ) -> bool:
        order = await self._require_order(order_id)
        if not authority.strip():
            raise CommerceError("authority is required")
        if status not in {"OK", "NOK"}:
            raise CommerceError("invalid provider callback status")
        if order.status is OrderStatus.PAID:
            return True
        payment = await self._repository.get_payment_by_order(order.id)
        if payment is None or payment.provider != provider_name:
            raise CommerceError("payment provider mismatch")
        if payment.amount != order.total_amount or payment.currency.upper() != order.currency.upper():
            raise CommerceError("payment amount mismatch")
        if payment.provider_reference and payment.provider_reference != authority:
            raise CommerceError("authority mismatch")
        if status == "NOK":
            payment.mark_failed()
            order.mark_payment_failed()
            await self._repository.save_payment(payment)
            await self._repository.save_order(order)
            await self._repository.commit()
            return False

        provider = self._provider(provider_name)
        result = await provider.verify_payment(
            PaymentVerificationRequest(
                payment_id=payment.id,
                order_id=order.id,
                authority=authority,
                amount=order.total_amount,
                currency=order.currency,
            )
        )
        if not result.success:
            payment.mark_failed()
            order.mark_payment_failed()
            await self._repository.save_payment(payment)
            await self._repository.save_order(order)
            await self._repository.commit()
            return False
        if not result.provider_reference:
            raise CommerceError("provider verification omitted reference")
        payment.mark_succeeded(result.provider_reference)
        payment.attempts[-1] = PaymentAttempt(
            provider=payment.attempts[-1].provider,
            amount=payment.attempts[-1].amount,
            currency=payment.attempts[-1].currency,
            status=PaymentAttemptStatus.VERIFIED,
            provider_reference=authority,
            idempotency_key=payment.attempts[-1].idempotency_key,
            metadata=dict(payment.attempts[-1].metadata) | dict(result.raw_metadata),
            created_at=payment.attempts[-1].created_at,
            verified_at=payment.verified_at,
        )
        order.mark_paid()
        await self._repository.save_payment(payment)
        await self._repository.save_order(order)
        await self._repository.commit()
        return True

    async def expire_order(self, order_id: UUID) -> Order:
        order = await self._require_order(order_id)
        if order.is_expired():
            order.expire()
        await self._repository.save_order(order)
        await self._repository.commit()
        return order

    async def _require_order(self, order_id: UUID) -> Order:
        order = await self._repository.get_order(order_id)
        if order is None:
            raise CommerceError("order not found")
        return order

    def _provider(self, name: str) -> PaymentProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise CommerceError("unsupported payment provider") from exc

    @staticmethod
    def _callback_url(base_url: str, order_id: UUID) -> str:
        if not base_url.strip():
            raise CommerceError("payment callback URL is required")
        parsed = urlsplit(base_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["order_id"] = str(order_id)
        return urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
        )

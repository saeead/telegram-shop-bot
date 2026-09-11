"""Pure commerce order and payment domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4


class OrderStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_PROCESSING = "payment_processing"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentAttemptStatus(StrEnum):
    CREATED = "created"
    REDIRECTED = "redirected"
    VERIFIED = "verified"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class OrderItem:
    product_id: UUID
    product_name: str
    unit_price: Decimal
    currency: str
    quantity: int = 1
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.product_name.strip():
            raise ValueError("product_name must not be empty")
        if self.unit_price < 0:
            raise ValueError("unit_price must not be negative")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True, slots=True)
class PaymentAttempt:
    provider: str
    amount: Decimal
    currency: str
    status: PaymentAttemptStatus = PaymentAttemptStatus.CREATED
    provider_reference: str | None = None
    idempotency_key: str = ""
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    verified_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        if self.amount < 0:
            raise ValueError("amount must not be negative")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")


@dataclass(slots=True)
class Payment:
    order_id: UUID
    provider: str
    amount: Decimal
    currency: str
    status: PaymentStatus = PaymentStatus.PENDING
    provider_reference: str | None = None
    attempts: list[PaymentAttempt] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    verified_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    def mark_processing(self) -> None:
        if self.status in {PaymentStatus.SUCCEEDED, PaymentStatus.REFUNDED}:
            return
        self.status = PaymentStatus.PROCESSING

    def mark_succeeded(self, reference: str, verified_at: datetime | None = None) -> None:
        if self.status is PaymentStatus.SUCCEEDED:
            return
        if not reference.strip():
            raise ValueError("provider reference must not be empty")
        self.provider_reference = reference
        self.status = PaymentStatus.SUCCEEDED
        self.verified_at = verified_at or datetime.now(UTC)

    def mark_failed(self) -> None:
        if self.status is not PaymentStatus.SUCCEEDED:
            self.status = PaymentStatus.FAILED


@dataclass(slots=True)
class Order:
    customer_telegram_id: int
    currency: str
    items: list[OrderItem]
    status: OrderStatus = OrderStatus.PENDING_PAYMENT
    expires_at: datetime | None = None
    idempotency_key: str = ""
    id: UUID = field(default_factory=uuid4)
    order_code: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.customer_telegram_id == 0:
            raise ValueError("customer_telegram_id must not be zero")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        if not self.items:
            raise ValueError("order must contain at least one item")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        if not self.order_code:
            self.order_code = f"ORD-{str(self.id).split('-')[0].upper()}"
        self.validate_currency()

    def validate_currency(self) -> None:
        if any(item.currency.upper() != self.currency.upper() for item in self.items):
            raise ValueError("all order items must use the order currency")

    @property
    def total_amount(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0"))

    def start_payment(self, payment: Payment) -> None:
        if self.is_expired():
            self.expire()
            raise ValueError("order has expired")
        if self.status is OrderStatus.PAID:
            raise ValueError("order is already paid")
        if self.status in {OrderStatus.CANCELLED, OrderStatus.EXPIRED}:
            raise ValueError("order is not payable")
        if payment.order_id != self.id:
            raise ValueError("payment does not belong to order")
        if payment.amount != self.total_amount or payment.currency.upper() != self.currency.upper():
            raise ValueError("payment amount or currency does not match order")
        self.status = OrderStatus.PAYMENT_PROCESSING
        self.updated_at = datetime.now(UTC)

    def mark_paid(self) -> None:
        if self.status is OrderStatus.PAID:
            return
        if self.status in {OrderStatus.CANCELLED, OrderStatus.EXPIRED}:
            raise ValueError("closed order cannot be marked paid")
        self.status = OrderStatus.PAID
        self.updated_at = datetime.now(UTC)

    def mark_payment_failed(self) -> None:
        if self.status is not OrderStatus.PAID:
            self.status = OrderStatus.PAYMENT_FAILED
            self.updated_at = datetime.now(UTC)

    def cancel(self) -> None:
        if self.status is not OrderStatus.PAID:
            self.status = OrderStatus.CANCELLED
            self.updated_at = datetime.now(UTC)

    def expire(self, now: datetime | None = None) -> None:
        if self.status is not OrderStatus.PAID:
            self.status = OrderStatus.EXPIRED
            self.updated_at = now or datetime.now(UTC)

    def is_expired(self, now: datetime | None = None) -> bool:
        return self.expires_at is not None and (now or datetime.now(UTC)) >= self.expires_at

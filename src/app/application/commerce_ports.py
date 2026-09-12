"""Application ports for orders and external payment providers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.domain.order import Order, Payment


@dataclass(frozen=True, slots=True)
class PaymentRequest:
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    currency: str
    description: str
    callback_url: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class PaymentRequestResult:
    provider: str
    authority: str
    payment_url: str
    raw_metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class PaymentVerificationRequest:
    payment_id: UUID
    order_id: UUID
    authority: str
    amount: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class PaymentVerificationResult:
    provider: str
    success: bool
    provider_reference: str | None
    already_verified: bool
    raw_metadata: dict[str, object]


class PaymentProvider(Protocol):
    name: str

    async def create_payment(self, request: PaymentRequest) -> PaymentRequestResult: ...

    async def verify_payment(
        self, request: PaymentVerificationRequest
    ) -> PaymentVerificationResult: ...

    async def refund(self, payment: Payment) -> str: ...


class CommerceRepositoryPort(Protocol):
    async def get_order(self, order_id: UUID) -> Order | None: ...

    async def get_order_by_idempotency_key(self, key: str) -> Order | None: ...

    async def save_order(self, order: Order) -> None: ...

    async def get_payment(self, payment_id: UUID) -> Payment | None: ...

    async def get_payment_by_order(self, order_id: UUID) -> Payment | None: ...

    async def get_payment_by_provider_reference(
        self, provider: str, reference: str
    ) -> Payment | None: ...

    async def save_payment(self, payment: Payment) -> None: ...

    async def commit(self) -> None: ...

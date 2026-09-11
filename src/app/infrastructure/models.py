"""SQLAlchemy persistence models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_code", name="uq_orders_order_code"),
        UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    order_code: Mapped[str] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    items: Mapped[list[OrderItemModel]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list[PaymentModel]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[UUID] = mapped_column(index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(String(3))
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped[OrderModel] = relationship(back_populates="items")


class PaymentModel(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_payments_order_id"),
        UniqueConstraint("provider", "provider_reference", name="uq_payments_provider_reference"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), index=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped[OrderModel] = relationship(back_populates="payments")
    attempts: Mapped[list[PaymentAttemptModel]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
        order_by="PaymentAttemptModel.created_at",
    )


class PaymentAttemptModel(Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_payment_attempts_idempotency_key"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    payment: Mapped[PaymentModel] = relationship(back_populates="attempts")

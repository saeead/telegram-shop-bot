"""SQLAlchemy persistence models for catalog, store, audit, and commerce state."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BIGINT,
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    product_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(String(3), default="IRR")
    status: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    files: Mapped[list[ProductFileModel]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductFileModel.ordering",
    )


class ProductFileModel(Base):
    __tablename__ = "product_files"
    __table_args__ = (
        UniqueConstraint(
            "telegram_chat_id",
            "telegram_message_id",
            name="uq_product_file_telegram_message",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    telegram_message_id: Mapped[int] = mapped_column(Integer)
    telegram_chat_id: Mapped[int] = mapped_column(Integer)
    file_type: Mapped[str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(32), index=True)
    original_filename: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ordering: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped[ProductModel] = relationship(back_populates="files")


class ProductIntakeModel(Base):
    __tablename__ = "product_intakes"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    state: Mapped[str] = mapped_column(String(64), index=True)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    admin_chat_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intake_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StorePublicationModel(Base):
    __tablename__ = "store_publications"
    __table_args__ = (UniqueConstraint("product_id", name="uq_store_publication_product"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    channel_id: Mapped[int] = mapped_column(Integer)
    media_message_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    cta_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str] = mapped_column(String(32), default="published", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    actor: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class OrderModel(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_code", name="uq_orders_order_code"),
        UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_telegram_id: Mapped[int] = mapped_column(BIGINT, index=True)
    order_code: Mapped[str] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(3))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    status: Mapped[str] = mapped_column(String(32), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
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
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[UUID] = mapped_column()
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


__all__ = [
    "AuditLogModel",
    "Base",
    "OrderItemModel",
    "OrderModel",
    "PaymentAttemptModel",
    "PaymentModel",
    "ProductFileModel",
    "ProductIntakeModel",
    "ProductModel",
    "StorePublicationModel",
]

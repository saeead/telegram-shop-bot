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

from app.domain.order import (
    OrderStatus,
    PaymentAttemptStatus,
    PaymentStatus,
)


class Base(DeclarativeBase):
    pass


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    product_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(String(3))
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    category: Mapped[CategoryModel | None] = relationship(back_populates="products")
    files: Mapped[list[ProductFileModel]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    tags: Mapped[list[ProductTagModel]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    products: Mapped[list[ProductModel]] = relationship(back_populates="category")


class ProductFileModel(Base):
    __tablename__ = "product_files"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    telegram_file_id: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))
    file_type: Mapped[str] = mapped_column(String(32))
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    product: Mapped[ProductModel] = relationship(back_populates="files")


class ProductTagModel(Base):
    __tablename__ = "product_tags"
    __table_args__ = (UniqueConstraint("product_id", "tag_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"))

    product: Mapped[ProductModel] = relationship(back_populates="tags")
    tag: Mapped[TagModel] = relationship(back_populates="products")


class TagModel(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    products: Mapped[list[ProductTagModel]] = relationship(back_populates="tag")


class StorePublicationModel(Base):
    __tablename__ = "store_publications"
    __table_args__ = (UniqueConstraint("product_id", "channel_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    channel_id: Mapped[int] = mapped_column(BIGINT)
    media_message_ids: Mapped[list[int]] = mapped_column(JSON)
    cta_message_id: Mapped[int] = mapped_column(Integer)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(BIGINT)
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[UUID] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class OrderModel(Base):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_telegram_id: Mapped[int] = mapped_column(BIGINT, index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(String(3))
    idempotency_key: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
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
    product_code: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(255))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(String(3))
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped[OrderModel] = relationship(back_populates="items")


class PaymentModel(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), index=True)
    authority: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

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
    "CategoryModel",
    "OrderItemModel",
    "OrderModel",
    "PaymentAttemptModel",
    "PaymentModel",
    "ProductFileModel",
    "ProductModel",
    "ProductTagModel",
    "StorePublicationModel",
    "TagModel",
]

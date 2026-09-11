"""SQLAlchemy persistence models for catalog, store, and audit state."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
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
    __table_args__ = (
        UniqueConstraint("product_id", name="uq_store_publication_product"),
    )

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


__all__ = [
    "AuditLogModel",
    "Base",
    "ProductFileModel",
    "ProductIntakeModel",
    "ProductModel",
    "StorePublicationModel",
]

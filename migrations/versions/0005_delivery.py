"""Add idempotent per-file delivery tracking.

Revision ID: 0005_delivery
Revises: 0004_orders_payment
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_delivery"
down_revision: str | Sequence[str] | None = "0004_orders_payment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "delivery_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=2000), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["product_files.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("order_id", "file_id", name="uq_delivery_order_file"),
    )
    op.create_index("ix_delivery_records_order_id", "delivery_records", ["order_id"])
    op.create_index("ix_delivery_records_product_id", "delivery_records", ["product_id"])
    op.create_index("ix_delivery_records_file_id", "delivery_records", ["file_id"])
    op.create_index("ix_delivery_records_status", "delivery_records", ["status"])
    op.create_index("ix_delivery_records_delivered_at", "delivery_records", ["delivered_at"])


def downgrade() -> None:
    op.drop_index("ix_delivery_records_delivered_at", table_name="delivery_records")
    op.drop_index("ix_delivery_records_status", table_name="delivery_records")
    op.drop_index("ix_delivery_records_file_id", table_name="delivery_records")
    op.drop_index("ix_delivery_records_product_id", table_name="delivery_records")
    op.drop_index("ix_delivery_records_order_id", table_name="delivery_records")
    op.drop_table("delivery_records")

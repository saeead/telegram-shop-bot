"""Product catalog and intake persistence.

Revision ID: 0002_product_intake
Revises: 0001_foundation
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_product_intake"
down_revision = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("price", sa.Numeric(20, 0), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="IRR"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=4000), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("product_code", name="uq_products_product_code"),
    )
    op.create_index("ix_products_product_code", "products", ["product_code"], unique=False)
    op.create_index("ix_products_status", "products", ["status"], unique=False)

    op.create_table(
        "product_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=512), nullable=True),
        sa.Column("telegram_message_id", sa.Integer(), nullable=False),
        sa.Column("telegram_chat_id", sa.Integer(), nullable=False),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.String(length=1024), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("telegram_chat_id", "telegram_message_id", name="uq_product_file_telegram_message"),
    )
    op.create_index("ix_product_files_product_id", "product_files", ["product_id"], unique=False)
    op.create_index("ix_product_files_role", "product_files", ["role"], unique=False)

    op.create_table(
        "product_intakes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column("admin_chat_id", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_product_intakes_product_id", "product_intakes", ["product_id"], unique=False)
    op.create_index("ix_product_intakes_state", "product_intakes", ["state"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_product_intakes_state", table_name="product_intakes")
    op.drop_index("ix_product_intakes_product_id", table_name="product_intakes")
    op.drop_table("product_intakes")
    op.drop_index("ix_product_files_role", table_name="product_files")
    op.drop_index("ix_product_files_product_id", table_name="product_files")
    op.drop_table("product_files")
    op.drop_index("ix_products_status", table_name="products")
    op.drop_index("ix_products_product_code", table_name="products")
    op.drop_table("products")

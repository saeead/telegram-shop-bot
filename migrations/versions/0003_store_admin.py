"""Store publication, visibility, and audit persistence.

Revision ID: 0003_store_admin
Revises: 0002_product_intake
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_store_admin"
down_revision = "0002_product_intake"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("products", "status", type_=sa.String(length=32))
    op.create_table(
        "store_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column(
            "media_message_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("cta_message_id", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="published"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("product_id", name="uq_store_publication_product"),
    )
    op.create_index("ix_store_publications_state", "store_publications", ["state"], unique=False)
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
    )
    op.create_index("ix_audit_logs_actor", "audit_logs", ["actor"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity"], unique=False)
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"], unique=False)
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_store_publications_state", table_name="store_publications")
    op.drop_table("store_publications")

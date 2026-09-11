"""Foundation migration with no business tables.

Revision ID: 0001_foundation
Revises:
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op

revision = "0001_foundation"
down_revision = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Phase 1 deliberately creates no Product, Order, Payment, or Customer tables.
    pass


def downgrade() -> None:
    pass

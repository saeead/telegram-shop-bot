"""Product intake state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class ProductIntakeState(StrEnum):
    RECEIVING = "receiving"
    CLASSIFYING = "classifying"
    WAITING_FOR_METADATA = "waiting_for_metadata"
    WAITING_FOR_ADMIN_CONFIRMATION = "waiting_for_admin_confirmation"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


_ALLOWED_TRANSITIONS: dict[ProductIntakeState, frozenset[ProductIntakeState]] = {
    ProductIntakeState.RECEIVING: frozenset(
        {ProductIntakeState.CLASSIFYING, ProductIntakeState.CANCELLED}
    ),
    ProductIntakeState.CLASSIFYING: frozenset(
        {
            ProductIntakeState.WAITING_FOR_METADATA,
            ProductIntakeState.FAILED,
            ProductIntakeState.CANCELLED,
        }
    ),
    ProductIntakeState.WAITING_FOR_METADATA: frozenset(
        {
            ProductIntakeState.WAITING_FOR_ADMIN_CONFIRMATION,
            ProductIntakeState.FAILED,
            ProductIntakeState.CANCELLED,
        }
    ),
    ProductIntakeState.WAITING_FOR_ADMIN_CONFIRMATION: frozenset(
        {
            ProductIntakeState.PUBLISHING,
            ProductIntakeState.CANCELLED,
            ProductIntakeState.FAILED,
        }
    ),
    ProductIntakeState.PUBLISHING: frozenset(
        {ProductIntakeState.PUBLISHED, ProductIntakeState.FAILED}
    ),
    ProductIntakeState.PUBLISHED: frozenset(),
    ProductIntakeState.FAILED: frozenset(),
    ProductIntakeState.CANCELLED: frozenset(),
}


@dataclass(slots=True)
class ProductIntake:
    product_id: UUID | None = None
    state: ProductIntakeState = ProductIntakeState.RECEIVING
    id: UUID = field(default_factory=uuid4)
    error_message: str | None = None

    def transition_to(self, target: ProductIntakeState) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"invalid intake transition: {self.state} -> {target}")
        self.state = target
        if target is not ProductIntakeState.FAILED:
            self.error_message = None

    def fail(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("failure reason must not be empty")
        self.transition_to(ProductIntakeState.FAILED)
        self.error_message = reason.strip()

    def attach_product(self, product_id: UUID) -> None:
        if self.state not in {
            ProductIntakeState.CLASSIFYING,
            ProductIntakeState.WAITING_FOR_METADATA,
            ProductIntakeState.WAITING_FOR_ADMIN_CONFIRMATION,
            ProductIntakeState.PUBLISHING,
            ProductIntakeState.PUBLISHED,
        }:
            raise ValueError("product cannot be attached in the current intake state")
        self.product_id = product_id

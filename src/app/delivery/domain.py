"""Pure delivery domain values."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PARTIAL = "partial"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass(slots=True)
class DeliveryRecord:
    order_id: UUID
    product_id: UUID
    file_id: UUID
    status: DeliveryStatus = DeliveryStatus.PENDING
    telegram_message_id: int | None = None
    attempt_count: int = 0
    delivered_at: datetime | None = None
    last_error: str | None = None
    id: UUID = field(default_factory=uuid4)

    def begin(self) -> None:
        if self.status is DeliveryStatus.DELIVERED:
            return
        self.status = DeliveryStatus.PROCESSING
        self.attempt_count += 1
        self.last_error = None

    def delivered(self, telegram_message_id: int) -> None:
        if telegram_message_id <= 0:
            raise ValueError("telegram_message_id must be positive")
        self.telegram_message_id = telegram_message_id
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = datetime.now(UTC)
        self.last_error = None

    def failed(self, error: str, partial: bool = False) -> None:
        self.last_error = error[:2000]
        self.status = DeliveryStatus.PARTIAL if partial else DeliveryStatus.FAILED


@dataclass(frozen=True, slots=True)
class DeliverySummary:
    order_id: UUID
    delivered: int
    pending: int
    failed: int
    status: DeliveryStatus

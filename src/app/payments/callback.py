"""Provider callback boundary; callback values are never trusted as payment proof."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PaymentCallback:
    order_id: UUID
    provider: str
    authority: str
    status: str


def parse_zarinpal_callback(query: dict[str, str]) -> PaymentCallback:
    raw_order_id = query.get("order_id", "").strip()
    authority = query.get("Authority", "").strip()
    status = query.get("Status", "").strip().upper()
    if not raw_order_id:
        raise ValueError("order_id is required")
    if not authority:
        raise ValueError("Authority is required")
    if status not in {"OK", "NOK"}:
        raise ValueError("Status must be OK or NOK")
    try:
        order_id = UUID(raw_order_id)
    except ValueError as exc:
        raise ValueError("order_id is invalid") from exc
    return PaymentCallback(
        order_id=order_id,
        provider="zarinpal",
        authority=authority,
        status=status,
    )

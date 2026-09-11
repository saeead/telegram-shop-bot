"""Versioned Telegram callback data builders and strict parsers."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CallbackData:
    version: int
    action: str
    value: str


def encode_callback(action: str, value: str) -> str:
    if not action or ":" in action or not value or ":" in value:
        raise ValueError("callback action and value must be non-empty and colon-free")
    return f"v1:{action}:{value}"


def parse_callback(data: str) -> CallbackData:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "v1" or not parts[1] or not parts[2]:
        raise ValueError("invalid callback data")
    try:
        version = int(parts[0][1:])
    except ValueError as exc:
        raise ValueError("invalid callback version") from exc
    if version != 1:
        raise ValueError("unsupported callback version")
    return CallbackData(version=version, action=parts[1], value=parts[2])


def product_callback(action: str, product_id: UUID) -> str:
    return encode_callback(action, str(product_id))

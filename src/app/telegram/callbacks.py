"""Versioned Telegram callback data builders and strict parsers."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, unquote
from uuid import UUID

_MAX_CALLBACK_BYTES = 64


@dataclass(frozen=True, slots=True)
class CallbackData:
    version: int
    action: str
    value: str


def encode_callback(action: str, value: str) -> str:
    if not action or ":" in action or not value:
        raise ValueError("callback action and value must be non-empty")
    encoded = f"v1:{action}:{quote(value, safe='')}"
    if len(encoded.encode("utf-8")) > _MAX_CALLBACK_BYTES:
        raise ValueError("callback data exceeds Telegram limit")
    return encoded


def parse_callback(data: str) -> CallbackData:
    if len(data.encode("utf-8")) > _MAX_CALLBACK_BYTES:
        raise ValueError("callback data exceeds Telegram limit")
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "v1" or not parts[1] or not parts[2]:
        raise ValueError("invalid callback data")
    try:
        version = int(parts[0][1:])
    except ValueError as exc:
        raise ValueError("invalid callback version") from exc
    if version != 1:
        raise ValueError("unsupported callback version")
    value = unquote(parts[2])
    if not value:
        raise ValueError("callback value must be non-empty")
    return CallbackData(version=version, action=parts[1], value=value)


def product_callback(action: str, product_id: UUID) -> str:
    return encode_callback(action, str(product_id))

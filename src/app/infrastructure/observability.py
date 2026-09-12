"""Small dependency-free observability primitives for the application core."""

from __future__ import annotations

import json
import logging
from collections import Counter
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")
_metrics: Counter[str] = Counter()


@dataclass(frozen=True, slots=True)
class CorrelationContext:
    correlation_id: str


def new_correlation_id() -> str:
    value = uuid4().hex
    _correlation_id.set(value)
    return value


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(value: str) -> None:
    if not value or len(value) > 128:
        raise ValueError("invalid correlation id")
    _correlation_id.set(value)


def increment_metric(name: str, value: int = 1) -> None:
    if value < 0:
        raise ValueError("metric increment must be non-negative")
    _metrics[name] += value


def snapshot_metrics() -> dict[str, int]:
    return dict(_metrics)


def clear_metrics() -> None:
    _metrics.clear()


def log_event(logger: logging.Logger, event: str, **fields: object) -> None:
    """Emit a named business event without accepting sensitive fields."""
    safe = {
        key: value
        for key, value in fields.items()
        if key.lower() not in StructuredJsonFormatter._SENSITIVE
        and not any(part in key.lower() for part in StructuredJsonFormatter._SENSITIVE)
    }
    logger.info("%s", event, extra={"event": event, **safe})


class StructuredJsonFormatter(logging.Formatter):
    """Emit machine-readable logs while filtering obvious secret fields."""

    _SENSITIVE = {"token", "secret", "password", "authorization", "merchant_id", "api_key"}

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        for key, value in record.__dict__.items():
            normalized = key.lower()
            if normalized in self._SENSITIVE or any(part in normalized for part in self._SENSITIVE):
                continue
            if key.startswith("_") or key in payload:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

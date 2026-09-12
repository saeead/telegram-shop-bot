import json
import logging

import pytest

from app.infrastructure.observability import (
    StructuredJsonFormatter,
    clear_metrics,
    get_correlation_id,
    increment_metric,
    new_correlation_id,
    snapshot_metrics,
)


def test_correlation_id_is_generated() -> None:
    value = new_correlation_id()
    assert value == get_correlation_id()
    assert len(value) == 32


def test_metrics_are_snapshotable() -> None:
    clear_metrics()
    increment_metric("orders_total")
    increment_metric("orders_total", 2)
    assert snapshot_metrics()["orders_total"] == 3
    clear_metrics()


def test_structured_formatter_drops_secrets() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "payment verified", (), None)
    record.api_token = "do-not-log"
    record.order_id = "order-1"
    output = json.loads(StructuredJsonFormatter().format(record))
    assert output["order_id"] == "order-1"
    assert "api_token" not in output


def test_negative_metric_increment_rejected() -> None:
    with pytest.raises(ValueError):
        increment_metric("orders_total", -1)

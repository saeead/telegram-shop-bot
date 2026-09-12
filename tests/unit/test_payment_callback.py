from uuid import uuid4

import pytest

from app.payments.callback import parse_zarinpal_callback


def test_callback_parser_validates_and_normalizes_status():
    order_id = uuid4()
    callback = parse_zarinpal_callback(
        {"order_id": str(order_id), "Authority": "AUTH-1", "Status": "ok"}
    )
    assert callback.order_id == order_id
    assert callback.provider == "zarinpal"
    assert callback.status == "OK"


@pytest.mark.parametrize(
    "query",
    [
        {"Authority": "AUTH-1", "Status": "OK"},
        {"order_id": "not-a-uuid", "Authority": "AUTH-1", "Status": "OK"},
        {"order_id": str(uuid4()), "Authority": "", "Status": "OK"},
        {"order_id": str(uuid4()), "Authority": "AUTH-1", "Status": "MAYBE"},
    ],
)
def test_callback_parser_rejects_untrusted_invalid_values(query):
    with pytest.raises(ValueError):
        parse_zarinpal_callback(query)

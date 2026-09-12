import pytest
from uuid import uuid4

from app.presentation.admin_router import _parse_uuid
from app.telegram.callbacks import parse_callback


def test_malformed_admin_product_identifier_is_rejected_without_exception() -> None:
    assert _parse_uuid("not-a-uuid") is None
    assert _parse_uuid("") is None
    assert _parse_uuid("../etc/passwd") is None


def test_valid_admin_product_identifier_is_accepted() -> None:
    product_id = uuid4()
    assert _parse_uuid(str(product_id)) == product_id


def test_oversized_or_malformed_callback_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_callback("v1:admin_product:" + ("x" * 200))
    with pytest.raises(ValueError):
        parse_callback("v1:admin_product:")


def test_callback_parser_does_not_turn_path_like_values_into_uuid() -> None:
    parsed = parse_callback("v1:admin_product:../../etc/passwd")
    assert parsed.value == "../../etc/passwd"
    assert _parse_uuid(parsed.value) is None

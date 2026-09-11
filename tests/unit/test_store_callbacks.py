from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.product import Category, Product, ProductFile, ProductFileRole, ProductFileType, Tag
from app.presentation.store import build_product_caption, preview_file_ids
from app.telegram.callbacks import encode_callback, parse_callback, product_callback


def make_product() -> Product:
    return Product(
        product_code="P-123",
        name="Dragon Model",
        price=Decimal(125000),
        category=Category("Fantasy:Models"),
        tags=[Tag("dragon")],
        files=[
            ProductFile("preview-1", 1, 2, ProductFileType.IMAGE, ProductFileRole.PREVIEW, None, "image/jpeg", 10),
            ProductFile("preview-2", 2, 2, ProductFileType.MEDIA, ProductFileRole.PREVIEW, None, "video/mp4", 20),
            ProductFile("secret-main", 3, 2, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "model.zip", "application/zip", 30),
        ],
    )


def test_versioned_callback_round_trip_and_uuid_callback():
    value = "Fantasy:Models"
    encoded = encode_callback("category", value)
    parsed = parse_callback(encoded)
    assert parsed.version == 1
    assert parsed.action == "category"
    assert parsed.value == value
    callback = product_callback("buy", uuid4())
    assert parse_callback(callback).action == "buy"


def test_invalid_callback_is_rejected():
    with pytest.raises(ValueError):
        parse_callback("v2:buy:123")
    with pytest.raises(ValueError):
        parse_callback("v1:buy")


def test_caption_and_preview_projection_never_include_main_file():
    product = make_product()
    caption = build_product_caption(product)
    assert "Dragon Model" in caption
    assert "P-123" in caption
    assert "secret-main" not in caption
    assert preview_file_ids(product) == ("preview-1", "preview-2")

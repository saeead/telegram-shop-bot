from decimal import Decimal

import pytest

from app.domain.intake import ProductIntake, ProductIntakeState
from app.domain.product import (
    Category,
    Product,
    ProductFile,
    ProductFileRole,
    ProductFileType,
    ProductStatus,
    Tag,
)


def make_file(message_id: int, role: ProductFileRole = ProductFileRole.MAIN) -> ProductFile:
    return ProductFile(
        telegram_file_id=f"file-{message_id}",
        telegram_message_id=message_id,
        telegram_chat_id=-100123,
        file_type=ProductFileType.DOCUMENT,
        role=role,
        original_filename="model.stl",
        mime_type="application/octet-stream",
        size=10,
    )


def test_product_aggregate_supports_multiple_previews_and_main_files() -> None:
    product = Product(
        product_code="p-ABC12345",
        name="Model",
        price=Decimal("250000"),
        category=Category("Animals"),
        tags=[Tag("stl"), Tag("toy")],
        files=[make_file(1, ProductFileRole.PREVIEW), make_file(2), make_file(3)],
    )

    assert len(product.previews) == 1
    assert len(product.main_files) == 2
    product.mark_ready()
    assert product.status is ProductStatus.READY


def test_product_rejects_duplicate_telegram_messages() -> None:
    with pytest.raises(ValueError, match="unique Telegram message IDs"):
        Product(
            product_code="P-DUPLICATE",
            name="Model",
            price=Decimal("1"),
            files=[make_file(1), make_file(1)],
        )


def test_product_requires_main_file_before_ready() -> None:
    product = Product(
        product_code="P-PREVIEWONLY",
        name="Preview",
        price=Decimal("1"),
        files=[make_file(1, ProductFileRole.PREVIEW)],
    )
    with pytest.raises(ValueError, match="at least one main file"):
        product.mark_ready()


def test_intake_state_machine_rejects_invalid_transition() -> None:
    intake = ProductIntake()
    intake.transition_to(ProductIntakeState.CLASSIFYING)
    intake.transition_to(ProductIntakeState.WAITING_FOR_METADATA)
    with pytest.raises(ValueError, match="invalid intake transition"):
        intake.transition_to(ProductIntakeState.PUBLISHED)

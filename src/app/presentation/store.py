"""Telegram Store presentation helpers; no Telegram dependency in the domain."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.domain.product import Product, ProductFileRole


def build_product_caption(product: Product) -> str:
    category = product.category.name if product.category else "-"
    tags = ", ".join(tag.name for tag in product.tags) or "-"
    return (
        f"{product.name}\n\n"
        f"Category: {category}\n"
        f"Tags: {tags}\n"
        f"Price: {_format_price(product.price)} {product.currency}\n"
        f"Code: {product.product_code}"
    )


def preview_file_ids(product: Product) -> tuple[str, ...]:
    return tuple(
        preview.file.telegram_file_id
        for preview in product.previews
        if preview.file.telegram_file_id and preview.file.role is ProductFileRole.PREVIEW
    )


def buy_callback(product_id: UUID) -> str:
    return f"v1:buy:{product_id}"


def _format_price(price: Decimal) -> str:
    return f"{price:,.0f}"

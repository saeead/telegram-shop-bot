"""Pure Product aggregate and product-related domain values."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4


class ProductStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ProductFileRole(StrEnum):
    PREVIEW = "preview"
    MAIN = "main"


class ProductFileType(StrEnum):
    IMAGE = "image"
    MEDIA = "media"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Category:
    name: str

    def __post_init__(self) -> None:
        value = self.name.strip()
        if not value:
            raise ValueError("category name must not be empty")
        object.__setattr__(self, "name", value)


@dataclass(frozen=True, slots=True)
class Tag:
    name: str

    def __post_init__(self) -> None:
        value = self.name.strip()
        if not value:
            raise ValueError("tag name must not be empty")
        object.__setattr__(self, "name", value)


@dataclass(frozen=True, slots=True)
class ProductFile:
    telegram_file_id: str | None
    telegram_message_id: int
    telegram_chat_id: int
    file_type: ProductFileType
    role: ProductFileRole
    original_filename: str | None
    mime_type: str | None
    size: int | None
    ordering: int = 0
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.telegram_message_id <= 0:
            raise ValueError("telegram_message_id must be positive")
        if self.telegram_chat_id == 0:
            raise ValueError("telegram_chat_id must not be zero")
        if self.ordering < 0:
            raise ValueError("ordering must not be negative")
        if self.size is not None and self.size < 0:
            raise ValueError("size must not be negative")


@dataclass(frozen=True, slots=True)
class ProductPreview:
    """Preview view over a ProductFile classified with the PREVIEW role."""

    file: ProductFile

    def __post_init__(self) -> None:
        if self.file.role is not ProductFileRole.PREVIEW:
            raise ValueError("ProductPreview requires a preview ProductFile")


@dataclass(slots=True)
class Product:
    product_code: str
    name: str
    price: Decimal
    currency: str = "IRR"
    category: Category | None = None
    tags: list[Tag] = field(default_factory=list)
    status: ProductStatus = ProductStatus.DRAFT
    description: str | None = None
    files: list[ProductFile] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.product_code = self.product_code.strip().upper()
        self.name = self.name.strip()
        self.currency = self.currency.strip().upper()
        self.validate()

    def validate(self) -> None:
        if not self.product_code:
            raise ValueError("product_code must not be empty")
        if not self.name:
            raise ValueError("product name must not be empty")
        if self.price < 0:
            raise ValueError("price must not be negative")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        if not self.files:
            raise ValueError("product must contain at least one file")
        codes = [file.telegram_message_id for file in self.files]
        if len(codes) != len(set(codes)):
            raise ValueError("product files must have unique Telegram message IDs")

    @property
    def previews(self) -> list[ProductPreview]:
        return [ProductPreview(file) for file in self.files if file.role is ProductFileRole.PREVIEW]

    @property
    def main_files(self) -> list[ProductFile]:
        return [file for file in self.files if file.role is ProductFileRole.MAIN]

    def add_file(self, product_file: ProductFile) -> None:
        if any(
            existing.telegram_message_id == product_file.telegram_message_id
            for existing in self.files
        ):
            raise ValueError("Telegram message already belongs to this product")
        self.files.append(product_file)
        self.validate()

    def set_category(self, category: Category) -> None:
        self.category = category

    def set_tags(self, tags: list[Tag]) -> None:
        self.tags = list(dict.fromkeys(tags))

    def mark_ready(self) -> None:
        self.validate()
        if not self.main_files:
            raise ValueError("product must contain at least one main file")
        self.status = ProductStatus.READY

    def mark_published(self) -> None:
        if self.status is not ProductStatus.READY:
            raise ValueError("only ready products can be published")
        self.status = ProductStatus.PUBLISHED

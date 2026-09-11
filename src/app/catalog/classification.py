"""Telegram intake file classification without Telegram SDK dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.product import ProductFileRole, ProductFileType


class IncomingMediaKind(StrEnum):
    PHOTO = "photo"
    DOCUMENT = "document"
    VIDEO = "video"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class IncomingFile:
    telegram_file_id: str | None
    telegram_message_id: int
    telegram_chat_id: int
    media_kind: IncomingMediaKind
    original_filename: str | None = None
    mime_type: str | None = None
    size: int | None = None


@dataclass(frozen=True, slots=True)
class ClassifiedFile:
    source: IncomingFile
    role: ProductFileRole
    file_type: ProductFileType
    ordering: int


MAIN_EXTENSIONS = frozenset({"stl", "zip", "rar", "7z"})
IMAGE_MIME_PREFIXES = ("image/",)


def classify_file(source: IncomingFile, ordering: int = 0) -> ClassifiedFile:
    extension = _extension(source.original_filename)
    if source.media_kind is IncomingMediaKind.PHOTO or (
        source.mime_type is not None and source.mime_type.lower().startswith(IMAGE_MIME_PREFIXES)
    ):
        return ClassifiedFile(source, ProductFileRole.PREVIEW, ProductFileType.IMAGE, ordering)

    if extension in MAIN_EXTENSIONS:
        file_type = ProductFileType.ARCHIVE if extension != "stl" else ProductFileType.DOCUMENT
        return ClassifiedFile(source, ProductFileRole.MAIN, file_type, ordering)

    if source.media_kind is IncomingMediaKind.DOCUMENT:
        return ClassifiedFile(source, ProductFileRole.MAIN, ProductFileType.DOCUMENT, ordering)

    return ClassifiedFile(source, ProductFileRole.MAIN, ProductFileType.UNKNOWN, ordering)


def classify_batch(files: list[IncomingFile]) -> list[ClassifiedFile]:
    if not files:
        raise ValueError("intake batch must contain at least one file")
    return [classify_file(item, index) for index, item in enumerate(files)]


def _extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower().strip()

from app.catalog.classification import (
    IncomingFile,
    IncomingMediaKind,
    classify_batch,
    classify_file,
)
from app.domain.product import ProductFileRole, ProductFileType


def incoming(message_id: int, kind: IncomingMediaKind, filename: str | None = None) -> IncomingFile:
    return IncomingFile(
        telegram_file_id=f"file-{message_id}",
        telegram_message_id=message_id,
        telegram_chat_id=-100123,
        media_kind=kind,
        original_filename=filename,
        mime_type="image/jpeg" if kind is IncomingMediaKind.PHOTO else None,
        size=100,
    )


def test_photo_is_preview() -> None:
    result = classify_file(incoming(1, IncomingMediaKind.PHOTO))
    assert result.role is ProductFileRole.PREVIEW
    assert result.file_type is ProductFileType.IMAGE


def test_video_is_media_preview() -> None:
    result = classify_file(incoming(1, IncomingMediaKind.VIDEO))
    assert result.role is ProductFileRole.PREVIEW
    assert result.file_type is ProductFileType.MEDIA


def test_supported_archives_and_stl_are_main_files() -> None:
    results = classify_batch(
        [
            incoming(1, IncomingMediaKind.DOCUMENT, "model.stl"),
            incoming(2, IncomingMediaKind.DOCUMENT, "set.zip"),
            incoming(3, IncomingMediaKind.DOCUMENT, "set.rar"),
            incoming(4, IncomingMediaKind.DOCUMENT, "set.7z"),
        ]
    )
    assert all(item.role is ProductFileRole.MAIN for item in results)
    assert results[1].file_type is ProductFileType.ARCHIVE


def test_empty_batch_is_invalid() -> None:
    try:
        classify_batch([])
    except ValueError as exc:
        assert "at least one file" in str(exc)
    else:
        raise AssertionError("empty intake batch must fail")

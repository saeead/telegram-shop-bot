from aiogram.types import Message

from app.catalog.classification import IncomingMediaKind
from app.telegram.intake_adapter import message_to_incoming_file


def test_document_message_translates_to_application_input() -> None:
    message = Message.model_validate(
        {
            "message_id": 77,
            "date": 1700000000,
            "chat": {"id": -100123, "type": "private"},
            "document": {
                "file_id": "telegram-file-id",
                "file_unique_id": "unique-id",
                "file_name": "model.stl",
                "mime_type": "application/octet-stream",
                "file_size": 123,
            },
        }
    )

    incoming = message_to_incoming_file(message)
    assert incoming is not None
    assert incoming.media_kind is IncomingMediaKind.DOCUMENT
    assert incoming.telegram_file_id == "telegram-file-id"
    assert incoming.original_filename == "model.stl"

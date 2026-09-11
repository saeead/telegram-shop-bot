"""aiogram boundary for translating Telegram messages into application input."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import Message

from app.catalog.classification import IncomingFile, IncomingMediaKind

router = Router(name="product-intake")


def message_to_incoming_file(message: Message) -> IncomingFile | None:
    if message.photo:
        photo = message.photo[-1]
        return IncomingFile(
            telegram_file_id=photo.file_id,
            telegram_message_id=message.message_id,
            telegram_chat_id=message.chat.id,
            media_kind=IncomingMediaKind.PHOTO,
            mime_type="image/jpeg",
            size=photo.file_size,
        )
    if message.video:
        return IncomingFile(
            telegram_file_id=message.video.file_id,
            telegram_message_id=message.message_id,
            telegram_chat_id=message.chat.id,
            media_kind=IncomingMediaKind.VIDEO,
            mime_type=message.video.mime_type,
            size=message.video.file_size,
        )
    if message.document:
        return IncomingFile(
            telegram_file_id=message.document.file_id,
            telegram_message_id=message.message_id,
            telegram_chat_id=message.chat.id,
            media_kind=IncomingMediaKind.DOCUMENT,
            original_filename=message.document.file_name,
            mime_type=message.document.mime_type,
            size=message.document.file_size,
        )
    return None

"""aiogram adapter that publishes previews only to the public Store channel."""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo

from app.application.store_ports import StorePublication
from app.domain.product import Product, ProductFileType
from app.presentation.store import build_product_caption, buy_callback, preview_file_ids


class TelegramStorePublisher:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def publish(self, product: Product, channel_id: int) -> StorePublication:
        previews = product.previews
        if not previews:
            raise ValueError("published product must contain at least one preview")
        media = []
        for index, preview in enumerate(previews):
            file_id = preview.file.telegram_file_id
            if not file_id:
                raise ValueError("preview is missing Telegram file id")
            if preview.file.file_type is ProductFileType.IMAGE:
                item = InputMediaPhoto(media=file_id)
            elif preview.file.file_type is ProductFileType.MEDIA:
                item = InputMediaVideo(media=file_id)
            else:
                raise ValueError("only image/video previews may be published")
            if index == 0:
                item.caption = build_product_caption(product)
            media.append(item)
        messages = await self._bot.send_media_group(chat_id=channel_id, media=media)
        cta = await self._bot.send_message(
            chat_id=channel_id,
            text="Ready to buy?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Buy",
                            callback_data=buy_callback(product.id),
                        )
                    ]
                ]
            ),
        )
        return StorePublication(
            product_id=product.id,
            channel_id=channel_id,
            media_message_ids=tuple(message.message_id for message in messages),
            cta_message_id=cta.message_id,
        )

    async def ensure_published(self, product: Product, channel_id: int) -> StorePublication:
        return await self.publish(product, channel_id)

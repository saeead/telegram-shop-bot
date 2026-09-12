"""aiogram adapter for copying private source messages to customers."""

from __future__ import annotations

from aiogram import Bot

from app.delivery.ports import DeliverySourcePort


class TelegramDeliverySource(DeliverySourcePort):
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def copy_to_customer(
        self,
        source_chat_id: int,
        source_message_id: int,
        customer_telegram_id: int,
    ) -> int:
        message = await self._bot.copy_message(
            chat_id=customer_telegram_id,
            from_chat_id=source_chat_id,
            message_id=source_message_id,
        )
        return message.message_id

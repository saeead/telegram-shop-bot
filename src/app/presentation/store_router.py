"""Public Telegram Store navigation handlers."""

from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.application.store_service import StoreService
from app.telegram.callbacks import encode_callback, parse_callback


def create_store_router(service: StoreService) -> Router:
    router = Router(name="public-store")

    @router.message(CommandStart())
    async def home(message: Message) -> None:
        await message.answer("Welcome to the Store.", reply_markup=_home_keyboard())

    @router.callback_query(F.data.startswith("v1:"))
    async def callback(callback: CallbackQuery) -> None:
        try:
            data = parse_callback(str(callback.data))
        except ValueError:
            await callback.answer("Invalid action", show_alert=True)
            return
        if data.action == "categories":
            await _answer_categories(callback, await service.categories())
            return
        if data.action == "tags":
            await _answer_tags(callback, await service.tags())
            return
        if data.action == "products":
            await _answer_products(callback, await service.products())
            return
        if data.action == "category":
            await _answer_products(callback, await service.products(category=data.value))
            return
        if data.action == "tag":
            await _answer_products(callback, await service.products(tag=data.value))
            return
        if data.action == "buy":
            await callback.answer("Purchase flow is not enabled in this phase.", show_alert=True)
            return
        await callback.answer("Unknown action", show_alert=True)

    return router


def _home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Categories", callback_data="v1:categories:home")],
            [InlineKeyboardButton(text="Tags", callback_data="v1:tags:home")],
            [InlineKeyboardButton(text="Products", callback_data="v1:products:all")],
        ]
    )


async def _answer_categories(callback: CallbackQuery, categories: list[str]) -> None:
    buttons = [
        [InlineKeyboardButton(text=category, callback_data=encode_callback("category", category))]
        for category in categories
    ]
    buttons.append([InlineKeyboardButton(text="Home", callback_data="v1:products:home")])
    if callback.message:
        await callback.message.answer(
            "Categories", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    await callback.answer()


async def _answer_tags(callback: CallbackQuery, tags: list[str]) -> None:
    buttons = [
        [InlineKeyboardButton(text=tag, callback_data=encode_callback("tag", tag))] for tag in tags
    ]
    buttons.append([InlineKeyboardButton(text="Home", callback_data="v1:products:home")])
    if callback.message:
        await callback.message.answer(
            "Tags", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    await callback.answer()


async def _answer_products(callback: CallbackQuery, products: list[Any]) -> None:
    if callback.message:
        if not products:
            await callback.message.answer("No products found.")
        else:
            await callback.message.answer(
                "\n".join(
                    f"{product.name} — {product.price} {product.currency}" for product in products
                )
            )
    await callback.answer()

"""Public Telegram Store navigation and purchase handlers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.commerce_service import CommerceError, CommerceService
from app.application.store_service import StoreService
from app.delivery.service import DeliveryError, DeliveryService
from app.telegram.callbacks import encode_callback, parse_callback, product_callback

SessionFactory = async_sessionmaker[AsyncSession]
StoreFactory = Callable[[AsyncSession], StoreService]
CommerceFactory = Callable[[AsyncSession], CommerceService]
DeliveryFactory = Callable[[AsyncSession], DeliveryService]


def create_store_router(
    session_factory: SessionFactory,
    store_factory: StoreFactory,
    commerce_factory: CommerceFactory,
    delivery_factory: DeliveryFactory,
    payment_callback_url: str,
    default_provider: str = "zarinpal",
) -> Router:
    router = Router(name="public-store")

    @router.message(CommandStart())
    async def home(message: Message) -> None:
        await message.answer("Welcome to the Store.", reply_markup=_home_keyboard())

    @router.message(Command("orders"))
    async def my_orders(message: Message) -> None:
        if message.from_user is None:
            return
        async with session_factory() as session:
            delivery = delivery_factory(session)
            orders = await delivery.get_history(message.from_user.id)
        if not orders:
            await message.answer("You have no orders yet.")
            return
        lines = [
            f"{order.order_code} — {order.status.value} — {order.total_amount} {order.currency}"
            for order in orders[:20]
        ]
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"Retry delivery {order.order_code}",
                    callback_data=encode_callback("retry", str(order.id)),
                )
            ]
            for order in orders[:10]
            if order.status.value == "paid"
        ]
        await message.answer(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
        )

    @router.callback_query(F.data.startswith("v1:"))
    async def callback(callback: CallbackQuery) -> None:
        try:
            data = parse_callback(str(callback.data))
        except ValueError:
            await callback.answer("Invalid action", show_alert=True)
            return
        if data.action == "categories":
            async with session_factory() as session:
                categories = await store_factory(session).categories()
            await _answer_categories(callback, categories)
            return
        if data.action == "tags":
            async with session_factory() as session:
                tags = await store_factory(session).tags()
            await _answer_tags(callback, tags)
            return
        if data.action == "products":
            async with session_factory() as session:
                products = await store_factory(session).products()
            await _answer_products(callback, products)
            return
        if data.action == "category":
            async with session_factory() as session:
                products = await store_factory(session).products(category=data.value)
            await _answer_products(callback, products)
            return
        if data.action == "tag":
            async with session_factory() as session:
                products = await store_factory(session).products(tag=data.value)
            await _answer_products(callback, products)
            return
        if data.action == "buy":
            await _handle_buy(
                callback,
                data.value,
                session_factory,
                commerce_factory,
                payment_callback_url,
                default_provider,
            )
            return
        if data.action == "retry":
            await _handle_retry(callback, data.value, session_factory, delivery_factory)
            return
        await callback.answer("Unknown action", show_alert=True)

    return router


async def _handle_buy(
    callback: CallbackQuery,
    raw_product_id: str,
    session_factory: SessionFactory,
    commerce_factory: CommerceFactory,
    payment_callback_url: str,
    default_provider: str,
) -> None:
    if callback.from_user is None:
        await callback.answer("Unauthorized", show_alert=True)
        return
    try:
        product_id = UUID(raw_product_id)
    except ValueError:
        await callback.answer("Invalid product", show_alert=True)
        return
    if not payment_callback_url.strip():
        await callback.answer("Payment is not configured", show_alert=True)
        return
    customer_id = callback.from_user.id
    idempotency_key = f"buy:{customer_id}:{product_id}"
    try:
        async with session_factory() as session:
            commerce = commerce_factory(session)
            order = await commerce.create_order(customer_id, product_id, 1, idempotency_key)
            payment = await commerce.create_payment(order.id, default_provider, payment_callback_url)
    except CommerceError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except Exception:
        await callback.answer("Payment could not be started", show_alert=True)
        return
    await callback.answer("Payment link created")
    if callback.message:
        await callback.message.answer(
            f"Order {order.order_code}\nAmount: {order.total_amount} {order.currency}\n"
            f"Pay here:\n{payment.payment_url}"
        )


async def _handle_retry(
    callback: CallbackQuery,
    raw_order_id: str,
    session_factory: SessionFactory,
    delivery_factory: DeliveryFactory,
) -> None:
    if callback.from_user is None:
        await callback.answer("Unauthorized", show_alert=True)
        return
    try:
        order_id = UUID(raw_order_id)
    except ValueError:
        await callback.answer("Invalid order", show_alert=True)
        return
    try:
        async with session_factory() as session:
            summary = await delivery_factory(session).retry(order_id, callback.from_user.id)
    except DeliveryError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.answer(f"Delivery status: {summary.status.value}")
    if callback.message:
        await callback.message.answer(
            f"Delivered {summary.delivered}, pending {summary.pending}, failed {summary.failed}."
        )


def _home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Categories", callback_data="v1:categories:home")],
            [InlineKeyboardButton(text="Tags", callback_data="v1:tags:home")],
            [InlineKeyboardButton(text="Products", callback_data="v1:products:all")],
        ]
    )


async def _answer_categories(callback: CallbackQuery, categories: list[str]) -> None:
    buttons: list[list[InlineKeyboardButton]] = []
    for category in categories:
        try:
            buttons.append(
                [InlineKeyboardButton(text=category, callback_data=encode_callback("category", category))]
            )
        except ValueError:
            continue
    buttons.append([InlineKeyboardButton(text="Home", callback_data="v1:products:home")])
    if callback.message:
        await callback.message.answer(
            "Categories", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    await callback.answer()


async def _answer_tags(callback: CallbackQuery, tags: list[str]) -> None:
    buttons: list[list[InlineKeyboardButton]] = []
    for tag in tags:
        try:
            buttons.append([InlineKeyboardButton(text=tag, callback_data=encode_callback("tag", tag))])
        except ValueError:
            continue
    buttons.append([InlineKeyboardButton(text="Home", callback_data="v1:products:home")])
    if callback.message:
        await callback.message.answer("Tags", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


async def _answer_products(callback: CallbackQuery, products: list[Any]) -> None:
    if callback.message:
        if not products:
            await callback.message.answer("No products found.")
        else:
            for product in products[:20]:
                text = f"{product.name} — {product.price} {product.currency}"
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Buy",
                                callback_data=product_callback("buy", product.id),
                            )
                        ]
                    ]
                )
                await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

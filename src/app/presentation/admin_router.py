"""Admin Telegram menu and product management handlers."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.application.store_service import ProductEdit, StoreService
from app.config.settings import Settings
from app.telegram.callbacks import parse_callback, product_callback


class AdminEditForm(StatesGroup):
    VALUE = State()


def create_admin_router(service: StoreService, settings: Settings) -> Router:
    router = Router(name="admin-store")

    def authorized(user_id: int | None) -> bool:
        return user_id is not None and user_id in settings.admin_ids

    @router.message(Command("admin"))
    async def admin_menu(message: Message) -> None:
        if not authorized(message.from_user.id if message.from_user else None):
            return
        await message.answer("Admin", reply_markup=_admin_keyboard())

    @router.callback_query(F.data.startswith("v1:admin_"))
    async def admin_callback(callback: CallbackQuery, state: FSMContext) -> None:
        actor = callback.from_user.id
        if not authorized(actor):
            await callback.answer("Unauthorized", show_alert=True)
            return
        try:
            data = parse_callback(str(callback.data))
        except ValueError:
            await callback.answer("Invalid action", show_alert=True)
            return
        if data.action == "admin_menu":
            if data.value == "products":
                products = await service.products()
                await callback.answer()
                if callback.message:
                    await callback.message.answer(
                        "Products",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text=product.name,
                                        callback_data=product_callback("admin_product", product.id),
                                    )
                                ]
                                for product in products
                            ]
                        ),
                    )
                return
            await callback.answer(f"{data.value.title()} management is available as a placeholder in this phase.")
            return
        if data.action == "admin_product":
            await _show_product(callback, service, actor, UUID(data.value))
            return
        await callback.answer("Unknown admin action", show_alert=True)

    @router.callback_query(F.data.startswith("v1:product_"))
    async def product_action(callback: CallbackQuery, state: FSMContext) -> None:
        actor = callback.from_user.id
        if not authorized(actor):
            await callback.answer("Unauthorized", show_alert=True)
            return
        try:
            data = parse_callback(str(callback.data))
        except ValueError:
            await callback.answer("Invalid action", show_alert=True)
            return
        if data.action not in {
            "product_hide",
            "product_republish",
            "product_details",
            "product_edit_price",
            "product_edit_name",
            "product_edit_category",
            "product_edit_tags",
        }:
            await callback.answer("Unknown product action", show_alert=True)
            return
        product_id = UUID(data.value)
        if data.action == "product_hide":
            await service.hide(actor, product_id)
            await callback.answer("Hidden")
        elif data.action == "product_details":
            product = await service.details(actor, product_id)
            await callback.answer("Details")
            if callback.message:
                await callback.message.answer(f"{product.name}\n{product.price} {product.currency}")
        elif data.action.startswith("product_edit_"):
            field = data.action.removeprefix("product_edit_")
            await state.update_data(product_id=str(product_id), field=field)
            await state.set_state(AdminEditForm.VALUE)
            await callback.answer(f"Edit {field}")
            if callback.message:
                await callback.message.answer(f"Enter the new {field}:")
        elif data.action == "product_republish":
            if settings.telegram_store_channel_id == 0:
                await callback.answer("Store channel is not configured", show_alert=True)
                return
            await service.republish(actor, product_id, settings.telegram_store_channel_id)
            await callback.answer("Republished")

    @router.message(AdminEditForm.VALUE)
    async def edit_product(message: Message, state: FSMContext) -> None:
        actor = message.from_user.id if message.from_user else None
        if actor is None or not authorized(actor):
            return
        data = await state.get_data()
        field = str(data.get("field", ""))
        value = message.text or ""
        try:
            if field == "price":
                changes = ProductEdit(price=Decimal(value.strip()))
            elif field == "name":
                changes = ProductEdit(name=value)
            elif field == "category":
                changes = ProductEdit(category=value)
            elif field == "tags":
                changes = ProductEdit(tags=tuple(tag.strip() for tag in value.split(",") if tag.strip()))
            else:
                raise ValueError("unsupported edit field")
            await service.edit(actor, UUID(str(data["product_id"])), changes)
        except (InvalidOperation, ValueError) as exc:
            await message.answer(str(exc) or "Invalid value.")
            return
        await state.clear()
        await message.answer(f"{field.title()} updated.")

    return router


def _admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Products", callback_data="v1:admin_menu:products")],
            [InlineKeyboardButton(text="Categories", callback_data="v1:admin_menu:categories")],
            [InlineKeyboardButton(text="Orders", callback_data="v1:admin_menu:orders")],
            [InlineKeyboardButton(text="Settings", callback_data="v1:admin_menu:settings")],
        ]
    )


async def _show_product(
    callback: CallbackQuery,
    service: StoreService,
    actor: int,
    product_id: UUID,
) -> None:
    product = await service.details(actor, product_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Edit price", callback_data=product_callback("product_edit_price", product.id))],
            [InlineKeyboardButton(text="Edit name", callback_data=product_callback("product_edit_name", product.id))],
            [InlineKeyboardButton(text="Edit category", callback_data=product_callback("product_edit_category", product.id))],
            [InlineKeyboardButton(text="Retag", callback_data=product_callback("product_edit_tags", product.id))],
            [InlineKeyboardButton(text="Hide", callback_data=product_callback("product_hide", product.id))],
            [InlineKeyboardButton(text="Republish", callback_data=product_callback("product_republish", product.id))],
            [InlineKeyboardButton(text="View details", callback_data=product_callback("product_details", product.id))],
        ]
    )
    if callback.message:
        await callback.message.answer(
            f"{product.name}\n{product.price} {product.currency}", reply_markup=keyboard
        )
    await callback.answer()

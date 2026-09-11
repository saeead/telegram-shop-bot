"""Admin-facing Product Intake FSM handlers."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.application.intake_service import ProductIntakeService, ProductMetadata
from app.application.telegram_ports import AdminReview
from app.catalog.classification import IncomingFile, IncomingMediaKind
from app.config.settings import Settings
from app.telegram.intake_adapter import message_to_incoming_file


class IntakeForm(StatesGroup):
    RECEIVING = State()
    NAME = State()
    CATEGORY = State()
    PRICE = State()
    TAGS = State()
    CONFIRMATION = State()


def create_intake_router(service: ProductIntakeService, settings: Settings) -> Router:
    router = Router(name="admin-product-intake")

    def is_admin(message: Message) -> bool:
        return message.from_user is not None and message.from_user.id in settings.admin_ids

    @router.message(Command("intake"))
    async def start_intake(message: Message, state: FSMContext) -> None:
        if not is_admin(message):
            return
        await state.clear()
        await state.set_state(IntakeForm.RECEIVING)
        await message.answer("Send the product previews/files, then send /done.")

    @router.message(IntakeForm.RECEIVING, Command("done"))
    async def finish_receiving(message: Message, state: FSMContext) -> None:
        if not is_admin(message):
            return
        data = await state.get_data()
        raw_files = data.get("files", [])
        files = [_deserialize_file(item) for item in raw_files if isinstance(item, dict)]
        if not files:
            await message.answer("No intake files received yet.")
            return
        intake = await service.receive_batch(message.chat.id, files)
        await state.update_data(intake_id=str(intake.id))
        await state.set_state(IntakeForm.NAME)
        await message.answer(f"Product code: {await _product_code(service, intake.id)}\nEnter product name:")

    @router.message(IntakeForm.RECEIVING)
    async def receive_file(message: Message, state: FSMContext) -> None:
        if not is_admin(message):
            return
        incoming = message_to_incoming_file(message)
        if incoming is None:
            await message.answer("Only photos, videos, or documents are accepted for intake.")
            return
        data = await state.get_data()
        files = list(data.get("files", []))
        files.append(_serialize_file(incoming))
        await state.update_data(files=files)
        await message.answer(f"Received item {len(files)}. Continue or send /done.")

    @router.message(IntakeForm.NAME)
    async def receive_name(message: Message, state: FSMContext) -> None:
        if not is_admin(message):
            return
        await state.update_data(name=message.text or "")
        await state.set_state(IntakeForm.CATEGORY)
        await message.answer("Enter category:")

    @router.message(IntakeForm.CATEGORY)
    async def receive_category(message: Message, state: FSMContext) -> None:
        if not is_admin(message):
            return
        await state.update_data(category=message.text or "")
        await state.set_state(IntakeForm.PRICE)
        await message.answer("Enter price in the configured currency (IRR by default):")

    @router.message(IntakeForm.PRICE)
    async def receive_price(message: Message, state: FSMContext) -> None:
        if not is_admin(message):
            return
        try:
            price = Decimal((message.text or "").strip())
        except InvalidOperation:
            await message.answer("Invalid price. Enter a numeric value.")
            return
        if price < 0:
            await message.answer("Price cannot be negative.")
            return
        await state.update_data(price=str(price))
        await state.set_state(IntakeForm.TAGS)
        await message.answer("Enter tags separated by commas, or /skip:")

    @router.message(IntakeForm.TAGS, Command("skip"))
    async def skip_tags(message: Message, state: FSMContext) -> None:
        await _finish_metadata(service, message, state, "")

    @router.message(IntakeForm.TAGS)
    async def receive_tags(message: Message, state: FSMContext) -> None:
        await _finish_metadata(service, message, state, message.text or "")

    @router.callback_query(IntakeForm.CONFIRMATION, F.data == "product:confirm")
    async def confirm(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        await service.confirm(_intake_id(data))
        await callback.answer("Published")
        if callback.message:
            await callback.message.answer("Product published successfully.")
        await state.clear()

    @router.callback_query(IntakeForm.CONFIRMATION, F.data == "product:cancel")
    async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        await service.cancel(_intake_id(data))
        await callback.answer("Cancelled")
        if callback.message:
            await callback.message.answer("Product intake cancelled.")
        await state.clear()

    @router.callback_query(IntakeForm.CONFIRMATION, F.data == "product:edit")
    async def edit(callback: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(IntakeForm.NAME)
        await callback.answer("Edit")
        if callback.message:
            await callback.message.answer("Enter the new product name:")

    return router


async def _finish_metadata(
    service: ProductIntakeService,
    message: Message,
    state: FSMContext,
    tags_text: str,
) -> None:
    data = await state.get_data()
    intake_id = UUID(str(data["intake_id"]))
    metadata = ProductMetadata(
        name=str(data.get("name", "")),
        category=str(data.get("category", "")),
        price=Decimal(str(data.get("price", "0"))),
        tags=tuple(tag.strip() for tag in tags_text.split(",") if tag.strip()),
    )
    review = await service.set_metadata(intake_id, metadata)
    await state.set_state(IntakeForm.CONFIRMATION)
    await message.answer(_format_review(review), reply_markup=_confirmation_keyboard())


def _confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Confirm", callback_data="product:confirm")],
            [InlineKeyboardButton(text="Edit", callback_data="product:edit")],
            [InlineKeyboardButton(text="Cancel", callback_data="product:cancel")],
        ]
    )


def _format_review(review: AdminReview) -> str:
    return (
        f"Product Code: {review.product_code}\n"
        f"Name: {review.name}\n"
        f"Category: {review.category}\n"
        f"Tags: {', '.join(review.tags) or '-'}\n"
        f"Price: {review.price} {review.currency}\n"
        f"Preview count: {review.preview_count}\n"
        f"Main file count: {review.main_file_count}"
    )


def _serialize_file(file: IncomingFile) -> dict[str, Any]:
    return {
        "telegram_file_id": file.telegram_file_id,
        "telegram_message_id": file.telegram_message_id,
        "telegram_chat_id": file.telegram_chat_id,
        "media_kind": file.media_kind.value,
        "original_filename": file.original_filename,
        "mime_type": file.mime_type,
        "size": file.size,
    }


def _deserialize_file(data: dict[str, Any]) -> IncomingFile:
    return IncomingFile(
        telegram_file_id=data.get("telegram_file_id"),
        telegram_message_id=int(data["telegram_message_id"]),
        telegram_chat_id=int(data["telegram_chat_id"]),
        media_kind=IncomingMediaKind(str(data["media_kind"])),
        original_filename=data.get("original_filename"),
        mime_type=data.get("mime_type"),
        size=int(data["size"]) if data.get("size") is not None else None,
    )


def _intake_id(data: dict[str, Any]) -> UUID:
    return UUID(str(data["intake_id"]))


async def _product_code(service: ProductIntakeService, intake_id: UUID) -> str:
    return (await service.review(intake_id)).product_code

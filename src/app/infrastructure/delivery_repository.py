"""SQLAlchemy persistence for per-file delivery tracking."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.delivery.domain import DeliveryRecord, DeliveryStatus
from app.delivery.ports import DeliveryRepositoryPort
from app.infrastructure.models import DeliveryRecordModel


class SqlAlchemyDeliveryRepository(DeliveryRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, order_id: UUID, file_id: UUID) -> DeliveryRecord | None:
        model = await self._session.scalar(
            select(DeliveryRecordModel).where(
                DeliveryRecordModel.order_id == order_id,
                DeliveryRecordModel.file_id == file_id,
            )
        )
        return self._to_domain(model) if model else None

    async def list_for_order(self, order_id: UUID) -> list[DeliveryRecord]:
        result = await self._session.scalars(
            select(DeliveryRecordModel)
            .where(DeliveryRecordModel.order_id == order_id)
            .order_by(DeliveryRecordModel.file_id)
        )
        return [self._to_domain(model) for model in result]

    async def save(self, record: DeliveryRecord) -> None:
        model = await self._session.get(DeliveryRecordModel, record.id)
        if model is None:
            model = DeliveryRecordModel(
                id=record.id,
                order_id=record.order_id,
                product_id=record.product_id,
                file_id=record.file_id,
                telegram_message_id=record.telegram_message_id,
                status=record.status.value,
                attempt_count=record.attempt_count,
                delivered_at=record.delivered_at,
                last_error=record.last_error,
            )
            self._session.add(model)
            return
        model.telegram_message_id = record.telegram_message_id
        model.status = record.status.value
        model.attempt_count = record.attempt_count
        model.delivered_at = record.delivered_at
        model.last_error = record.last_error

    async def commit(self) -> None:
        await self._session.commit()

    @staticmethod
    def _to_domain(model: DeliveryRecordModel) -> DeliveryRecord:
        return DeliveryRecord(
            id=model.id,
            order_id=model.order_id,
            product_id=model.product_id,
            file_id=model.file_id,
            telegram_message_id=model.telegram_message_id,
            status=DeliveryStatus(model.status),
            attempt_count=model.attempt_count,
            delivered_at=model.delivered_at,
            last_error=model.last_error,
        )

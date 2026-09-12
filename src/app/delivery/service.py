"""Application orchestration for secure, retryable customer delivery."""

from __future__ import annotations

from uuid import UUID

from app.application.catalog_ports import ProductRepository
from app.application.commerce_ports import CommerceRepositoryPort
from app.delivery.domain import DeliveryRecord, DeliveryStatus, DeliverySummary
from app.delivery.ports import (
    DeliveryLockPort,
    DeliveryRepositoryPort,
    DeliverySourceError,
    DeliverySourcePort,
)
from app.domain.order import Order, OrderStatus
from app.domain.product import ProductFile


class DeliveryError(ValueError):
    """Expected delivery validation failure."""


class DeliveryService:
    def __init__(
        self,
        products: ProductRepository,
        commerce: CommerceRepositoryPort,
        repository: DeliveryRepositoryPort,
        source: DeliverySourcePort,
        lock: DeliveryLockPort | None = None,
        archive_channel_id: int = 0,
        backup_channel_id: int = 0,
    ) -> None:
        self._products = products
        self._commerce = commerce
        self._repository = repository
        self._source = source
        self._lock = lock
        self._source_channels = tuple(
            channel for channel in (archive_channel_id, backup_channel_id) if channel
        )

    async def deliver(self, order_id: UUID, customer_telegram_id: int) -> DeliverySummary:
        order = await self._commerce.get_order(order_id)
        if order is None:
            raise DeliveryError("order not found")
        if order.customer_telegram_id != customer_telegram_id:
            raise DeliveryError("order does not belong to customer")
        if order.status is not OrderStatus.PAID:
            raise DeliveryError("order is not paid")

        lock_key = f"delivery:order:{order_id}"
        acquired = True
        if self._lock is not None:
            acquired = await self._lock.acquire_lock(lock_key, ttl_seconds=300)
        if not acquired:
            raise DeliveryError("delivery is already processing")

        try:
            for item in order.items:
                product = await self._products.get(item.product_id)
                if product is None:
                    raise DeliveryError("purchased product is unavailable")
                await self._deliver_product(
                    order_id, customer_telegram_id, product.id, product.main_files
                )
            return await self._summary(order_id)
        finally:
            if self._lock is not None and acquired:
                await self._lock.release_lock(lock_key)

    async def retry(self, order_id: UUID, customer_telegram_id: int) -> DeliverySummary:
        return await self.deliver(order_id, customer_telegram_id)

    async def get_history(self, customer_telegram_id: int) -> list[Order]:
        return await self._commerce.list_orders_for_customer(customer_telegram_id)

    async def get_order_details(self, order_id: UUID, customer_telegram_id: int) -> Order:
        order = await self._commerce.get_order(order_id)
        if order is None or order.customer_telegram_id != customer_telegram_id:
            raise DeliveryError("order not found")
        return order

    async def validate_product_code(
        self, product_code: str, order_id: UUID, customer_telegram_id: int
    ) -> UUID:
        order = await self.get_order_details(order_id, customer_telegram_id)
        product = await self._products.get_by_code(product_code.strip().upper())
        if product is None or product.id not in {item.product_id for item in order.items}:
            raise DeliveryError("product is not part of this order")
        if order.status is not OrderStatus.PAID:
            raise DeliveryError("order is not paid")
        return product.id

    async def _deliver_product(
        self,
        order_id: UUID,
        customer_telegram_id: int,
        product_id: UUID,
        files: list[ProductFile],
    ) -> None:
        ordered_files = sorted(files, key=lambda item: (item.ordering, str(item.id)))
        existing = {record.file_id: record for record in await self._repository.list_for_order(order_id)}
        records: list[DeliveryRecord] = []
        for file in ordered_files:
            record = existing.get(file.id)
            if record is None:
                record = DeliveryRecord(order_id=order_id, product_id=product_id, file_id=file.id)
                await self._repository.save(record)
            records.append(record)

        for record, file in zip(records, ordered_files, strict=True):
            if record.status is DeliveryStatus.DELIVERED:
                continue
            record.begin()
            await self._repository.save(record)
            try:
                message_id = await self._copy_with_fallback(file, customer_telegram_id)
            except (DeliverySourceError, TimeoutError) as exc:
                partial = any(r.status is DeliveryStatus.DELIVERED for r in records)
                record.failed(self._safe_error(exc), partial=partial)
                await self._repository.save(record)
                await self._repository.commit()
                continue
            record.delivered(message_id)
            await self._repository.save(record)
            await self._repository.commit()

    async def _copy_with_fallback(self, file: ProductFile, customer_telegram_id: int) -> int:
        channels = self._source_channels or (file.telegram_chat_id,)
        if file.telegram_chat_id in channels:
            channels = (file.telegram_chat_id,) + tuple(
                channel for channel in channels if channel != file.telegram_chat_id
            )
        last_error: DeliverySourceError | TimeoutError | None = None
        for channel_id in channels:
            try:
                return await self._source.copy_to_customer(
                    channel_id, file.telegram_message_id, customer_telegram_id
                )
            except (DeliverySourceError, TimeoutError) as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise DeliveryError("no delivery source configured")

    async def _summary(self, order_id: UUID) -> DeliverySummary:
        records = await self._repository.list_for_order(order_id)
        delivered = sum(record.status is DeliveryStatus.DELIVERED for record in records)
        failed = sum(record.status in {DeliveryStatus.FAILED, DeliveryStatus.PARTIAL} for record in records)
        pending = len(records) - delivered - failed
        if records and delivered == len(records):
            status = DeliveryStatus.DELIVERED
        elif delivered:
            status = DeliveryStatus.PARTIAL
        elif failed:
            status = DeliveryStatus.FAILED
        else:
            status = DeliveryStatus.PENDING
        return DeliverySummary(order_id, delivered, pending, failed, status)

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        text = str(exc).strip()
        return text[:2000] if text else exc.__class__.__name__

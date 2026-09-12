"""Application composition root for runtime wiring."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.commerce_ports import PaymentProvider
from app.application.commerce_service import CommerceService
from app.application.intake_service import (
    ProductIntakeService,
    ProductPublisherPort,
    PublicationError,
)
from app.application.store_service import AdminAuthorizer, StoreService
from app.config.settings import Settings
from app.delivery.service import DeliveryService
from app.domain.product import Product
from app.infrastructure.commerce_repository import SqlAlchemyCommerceRepository
from app.infrastructure.database import create_engine, create_session_factory
from app.infrastructure.delivery_repository import SqlAlchemyDeliveryRepository
from app.infrastructure.product_repository import SqlAlchemyProductRepository
from app.infrastructure.redis import RedisStore, create_redis_store
from app.payments.zarinpal import ZarinpalProvider
from app.telegram.delivery_source import TelegramDeliverySource
from app.telegram.store_publisher import TelegramStorePublisher


@dataclass(slots=True)
class AppRuntime:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    redis: RedisStore
    bot: Bot
    dispatcher: Dispatcher

    def commerce_service(self, session: AsyncSession) -> CommerceService:
        products = SqlAlchemyProductRepository(session)
        commerce = SqlAlchemyCommerceRepository(session)
        providers: dict[str, PaymentProvider] = {}
        if self.settings.zarinpal_merchant_id.strip():
            providers["zarinpal"] = ZarinpalProvider(
                merchant_id=self.settings.zarinpal_merchant_id,
                sandbox=self.settings.zarinpal_sandbox,
            )
        return CommerceService(products, commerce, providers)

    def delivery_service(self, session: AsyncSession) -> DeliveryService:
        return DeliveryService(
            products=SqlAlchemyProductRepository(session),
            commerce=SqlAlchemyCommerceRepository(session),
            repository=SqlAlchemyDeliveryRepository(session),
            source=TelegramDeliverySource(self.bot),
            lock=self.redis,
            archive_channel_id=self.settings.telegram_archive_channel_id,
            backup_channel_id=self.settings.telegram_backup_channel_id,
        )

    def store_service(self, session: AsyncSession) -> StoreService:
        return StoreService(
            repository=SqlAlchemyProductRepository(session),
            publisher=TelegramStorePublisher(self.bot),
            authorizer=AdminAuthorizer(self.settings.admin_ids),
        )

    def intake_service(self, session: AsyncSession) -> ProductIntakeService:
        return ProductIntakeService(
            repository=SqlAlchemyProductRepository(session),
            cache=self.redis,
            publisher=_ConfirmedProductPublisher(self, session),
        )

    async def close(self) -> None:
        await self.redis.close()
        await self.engine.dispose()
        await self.bot.session.close()


class _ConfirmedProductPublisher(ProductPublisherPort):
    def __init__(self, runtime: AppRuntime, session: AsyncSession) -> None:
        self._runtime = runtime
        self._session = session

    async def publish(self, product: Product) -> None:
        channel_id = self._runtime.settings.telegram_store_channel_id
        if channel_id == 0:
            raise PublicationError("TELEGRAM_STORE_CHANNEL_ID is not configured")
        actor = next(iter(self._runtime.settings.admin_ids), 0)
        if actor == 0:
            raise PublicationError("TELEGRAM_ADMIN_IDS is not configured")
        try:
            await self._runtime.store_service(self._session).publish(actor, product.id, channel_id)
        except (ValueError, RuntimeError, OSError, PermissionError) as exc:
            raise PublicationError(str(exc)) from exc


def build_runtime(settings: Settings) -> AppRuntime:
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    redis = create_redis_store(settings.redis_url)
    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher(storage=MemoryStorage())
    return AppRuntime(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        redis=redis,
        bot=bot,
        dispatcher=dispatcher,
    )

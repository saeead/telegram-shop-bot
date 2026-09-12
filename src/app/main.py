"""Process entrypoint: configuration validation and production runtime."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.intake_service import ProductIntakeService
from app.application.store_service import StoreService
from app.bootstrap import AppRuntime, build_runtime
from app.config.settings import Settings, get_settings
from app.infrastructure.logging.setup import configure_logging
from app.presentation.admin_router import create_admin_router
from app.presentation.intake import create_intake_router
from app.presentation.payment_webhook import create_payment_app_from_runtime
from app.presentation.store_router import create_store_router

logger = logging.getLogger(__name__)

SessionFactory = async_sessionmaker[AsyncSession]
StoreFactory = Callable[[AsyncSession], StoreService]
IntakeFactory = Callable[[AsyncSession], ProductIntakeService]


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Application configuration validated")
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    if settings.app_env == "test":
        return
    asyncio.run(run_application(settings))


async def run_application(settings: Settings) -> None:
    runtime = build_runtime(settings)
    try:
        _register_routers(runtime)
        runner: web.AppRunner | None = None
        site: web.TCPSite | None = None
        if settings.payment_callback_url.strip():
            app = create_payment_app_from_runtime(runtime)
            host, port = _callback_bind(settings.payment_callback_url)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host=host, port=port)
            await site.start()
            logger.info("Payment callback server listening on %s:%s", host, port)
        logger.info("Starting Telegram polling")
        await runtime.dispatcher.start_polling(runtime.bot)
    finally:
        if site is not None and runner is not None:
            await runner.cleanup()
        await runtime.close()


def _register_routers(runtime: AppRuntime) -> None:
    settings = runtime.settings
    session_factory = runtime.session_factory

    def session_store(session: AsyncSession) -> StoreService:
        return runtime.store_service(session)

    def session_commerce(session: AsyncSession) -> Any:
        return runtime.commerce_service(session)

    def session_delivery(session: AsyncSession) -> Any:
        return runtime.delivery_service(session)

    def session_intake(session: AsyncSession) -> ProductIntakeService:
        return runtime.intake_service(session)

    runtime.dispatcher.include_router(
        create_store_router(
            session_factory,
            session_store,
            session_commerce,
            session_delivery,
            settings.payment_callback_url,
            default_provider="zarinpal",
        )
    )
    runtime.dispatcher.include_router(_wrap_admin_router(session_factory, session_store, settings))
    runtime.dispatcher.include_router(
        _wrap_intake_router(session_factory, session_intake, settings)
    )


def _wrap_admin_router(
    session_factory: SessionFactory,
    store_factory: StoreFactory,
    settings: Settings,
) -> Any:
    """Admin router expects a long-lived service; bridge with session-scoped proxy."""

    class _SessionStoreProxy:
        def __getattr__(self, name: str) -> Callable[..., Any]:
            async def method(*args: Any, **kwargs: Any) -> Any:
                async with session_factory() as session:
                    service = store_factory(session)
                    result = getattr(service, name)(*args, **kwargs)
                    if asyncio.iscoroutine(result):
                        return await result
                    return result

            return method

    return create_admin_router(_SessionStoreProxy(), settings)  # type: ignore[arg-type]


def _wrap_intake_router(
    session_factory: SessionFactory,
    intake_factory: IntakeFactory,
    settings: Settings,
) -> Any:
    class _SessionIntakeProxy:
        def __getattr__(self, name: str) -> Callable[..., Any]:
            async def method(*args: Any, **kwargs: Any) -> Any:
                async with session_factory() as session:
                    service = intake_factory(session)
                    result = getattr(service, name)(*args, **kwargs)
                    if asyncio.iscoroutine(result):
                        return await result
                    return result

            return method

    return create_intake_router(_SessionIntakeProxy(), settings)  # type: ignore[arg-type]


def _callback_bind(callback_url: str) -> tuple[str, int]:
    parsed = urlsplit(callback_url)
    host = "0.0.0.0"
    port = parsed.port or (443 if parsed.scheme == "https" else 8080)
    return host, port


if __name__ == "__main__":
    main()

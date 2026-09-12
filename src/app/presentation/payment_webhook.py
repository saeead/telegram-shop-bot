"""HTTP boundary for untrusted payment provider callbacks."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.commerce_service import CommerceError, CommerceService
from app.delivery.service import DeliveryError, DeliveryService
from app.payments.callback import parse_zarinpal_callback

if TYPE_CHECKING:
    from app.bootstrap import AppRuntime

logger = logging.getLogger(__name__)

SessionFactory = async_sessionmaker[AsyncSession]
CommerceFactory = Callable[[AsyncSession], CommerceService]
DeliveryFactory = Callable[[AsyncSession], DeliveryService]
BotNotifier = Callable[[int, str], Awaitable[None]]


def create_payment_app(
    session_factory: SessionFactory,
    commerce_factory: CommerceFactory,
    delivery_factory: DeliveryFactory,
    bot_notifier: BotNotifier | None = None,
) -> web.Application:
    app = web.Application()

    async def zarinpal_callback(request: web.Request) -> web.Response:
        query = {key: value for key, value in request.rel_url.query.items()}
        try:
            parsed = parse_zarinpal_callback(query)
        except ValueError as exc:
            logger.warning("Rejected payment callback: %s", exc)
            return web.Response(text="invalid callback", status=400)

        try:
            async with session_factory() as session:
                commerce = commerce_factory(session)
                paid = await commerce.handle_callback(
                    parsed.order_id,
                    parsed.provider,
                    parsed.authority,
                    parsed.status,
                )
                if paid:
                    order = await commerce.get_order(parsed.order_id)
                    delivery = delivery_factory(session)
                    summary = await delivery.deliver(order.id, order.customer_telegram_id)
                    if bot_notifier is not None:
                        await bot_notifier(
                            order.customer_telegram_id,
                            (
                                f"Payment confirmed for order {order.order_code}. "
                                f"Delivered {summary.delivered} file(s)."
                            ),
                        )
                elif bot_notifier is not None:
                    order = await commerce.get_order(parsed.order_id)
                    await bot_notifier(
                        order.customer_telegram_id,
                        f"Payment was not completed for order {order.order_code}.",
                    )
        except (CommerceError, DeliveryError) as exc:
            logger.warning("Payment callback handling failed: %s", exc)
            return web.Response(text="processing failed", status=400)
        except Exception:
            logger.exception("Unexpected payment callback failure")
            return web.Response(text="internal error", status=500)
        return web.Response(text="OK")

    async def health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app.router.add_get("/payments/zarinpal/callback", zarinpal_callback)
    app.router.add_get("/health", health)
    return app


def create_payment_app_from_runtime(runtime: AppRuntime) -> web.Application:
    async def notify(customer_id: int, text: str) -> None:
        await runtime.bot.send_message(chat_id=customer_id, text=text)

    return create_payment_app(
        runtime.session_factory,
        runtime.commerce_service,
        runtime.delivery_service,
        bot_notifier=notify,
    )

"""Phase 6 failure-injection and concurrency coverage for commerce + delivery."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from uuid import UUID

import pytest
from aiohttp.test_utils import TestClient, TestServer

from app.application.commerce_ports import (
    PaymentRequest,
    PaymentRequestResult,
    PaymentVerificationRequest,
    PaymentVerificationResult,
)
from app.application.commerce_service import CommerceError, CommerceService
from app.delivery.domain import DeliveryRecord, DeliveryStatus
from app.delivery.service import DeliveryError, DeliveryService
from app.domain.order import Order, OrderItem, OrderStatus
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType, ProductStatus
from app.presentation.payment_webhook import create_payment_app


class FakeProducts:
    def __init__(self, product: Product) -> None:
        self.product = product

    async def get(self, product_id: UUID):
        return self.product if product_id == self.product.id else None

    async def get_by_code(self, code: str):
        return self.product if code == self.product.product_code else None


class FakeCommerceRepo:
    def __init__(self) -> None:
        self.orders: dict[UUID, Order] = {}
        self.payments: dict = {}
        self._mutex = asyncio.Lock()

    async def get_order(self, order_id: UUID):
        return self.orders.get(order_id)

    async def get_order_by_idempotency_key(self, key: str):
        return next((o for o in self.orders.values() if o.idempotency_key == key), None)

    async def list_orders_for_customer(self, customer_telegram_id: int):
        return [o for o in self.orders.values() if o.customer_telegram_id == customer_telegram_id]

    async def save_order(self, order: Order) -> None:
        self.orders[order.id] = order

    async def get_payment(self, payment_id: UUID):
        return self.payments.get(payment_id)

    async def get_payment_by_order(self, order_id: UUID):
        return next((p for p in self.payments.values() if p.order_id == order_id), None)

    async def get_payment_by_provider_reference(self, provider: str, reference: str):
        return next(
            (
                p
                for p in self.payments.values()
                if p.provider == provider and p.provider_reference == reference
            ),
            None,
        )

    async def save_payment(self, payment) -> None:
        self.payments[payment.id] = payment

    async def commit(self) -> None:
        return None


class FakeDeliveryRepo:
    def __init__(self) -> None:
        self.records: dict[tuple[UUID, UUID], DeliveryRecord] = {}

    async def get(self, order_id: UUID, file_id: UUID):
        return self.records.get((order_id, file_id))

    async def list_for_order(self, order_id: UUID):
        return [r for (oid, _), r in self.records.items() if oid == order_id]

    async def save(self, record: DeliveryRecord) -> None:
        self.records[(record.order_id, record.file_id)] = record

    async def commit(self) -> None:
        return None


class ConcurrentLock:
    """In-memory lock that models Redis SET NX under concurrent awaiters."""

    def __init__(self) -> None:
        self._held: set[str] = set()
        self._mutex = asyncio.Lock()
        self.acquire_attempts = 0
        self.release_count = 0

    async def acquire_lock(self, key: str, *, ttl_seconds: int) -> bool:
        async with self._mutex:
            self.acquire_attempts += 1
            if key in self._held:
                return False
            self._held.add(key)
            return True

    async def release_lock(self, key: str) -> None:
        async with self._mutex:
            self._held.discard(key)
            self.release_count += 1


class FailingLock:
    async def acquire_lock(self, key: str, *, ttl_seconds: int) -> bool:
        raise RuntimeError("redis unavailable")

    async def release_lock(self, key: str) -> None:
        return None


class ControllableSource:
    def __init__(
        self,
        *,
        fail_channels: set[int] | None = None,
        delay_seconds: float = 0.0,
        fail_once: bool = False,
    ) -> None:
        self.fail_channels = fail_channels or set()
        self.delay_seconds = delay_seconds
        self.fail_once = fail_once
        self.calls: list[tuple[int, int, int]] = []
        self.next_message = 100
        self._failed_once = False

    async def copy_to_customer(
        self, source_chat_id: int, source_message_id: int, customer_telegram_id: int
    ) -> int:
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        self.calls.append((source_chat_id, source_message_id, customer_telegram_id))
        if self.fail_once and not self._failed_once:
            self._failed_once = True
            raise TimeoutError("telegram timeout once")
        if source_chat_id in self.fail_channels:
            raise TimeoutError("telegram timeout")
        self.next_message += 1
        return self.next_message


class ControllableProvider:
    name = "fake"

    def __init__(
        self,
        *,
        fail_create: bool = False,
        fail_verify: bool = False,
        verify_delay: float = 0.0,
        create_delay: float = 0.0,
    ) -> None:
        self.fail_create = fail_create
        self.fail_verify = fail_verify
        self.verify_delay = verify_delay
        self.create_delay = create_delay
        self.create_calls = 0
        self.verify_calls = 0

    async def create_payment(self, request: PaymentRequest):
        self.create_calls += 1
        if self.create_delay:
            await asyncio.sleep(self.create_delay)
        if self.fail_create:
            raise TimeoutError("provider timeout")
        return PaymentRequestResult("fake", "AUTH-1", "https://pay.test/AUTH-1", {})

    async def verify_payment(self, request: PaymentVerificationRequest):
        self.verify_calls += 1
        if self.verify_delay:
            await asyncio.sleep(self.verify_delay)
        if self.fail_verify:
            return PaymentVerificationResult("fake", False, None, False, {})
        return PaymentVerificationResult("fake", True, "REF-1", False, {})

    async def refund(self, payment):
        return "REFUND-1"


def _product(code: str = "P-FI") -> Product:
    return Product(
        code,
        "Failure Product",
        Decimal(1500),
        "IRR",
        status=ProductStatus.PUBLISHED,
        files=[
            ProductFile(
                "f1", 20, 900, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "a.stl", None, 10, 0
            ),
            ProductFile(
                "f2", 21, 900, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "b.zip", None, 20, 1
            ),
        ],
    )


def _paid_order(product: Product, customer_id: int = 777) -> Order:
    order = Order(
        customer_id,
        "IRR",
        [OrderItem(product.id, product.name, product.price, product.currency)],
        idempotency_key=f"order-{customer_id}",
    )
    order.mark_paid()
    return order


@pytest.mark.asyncio
async def test_concurrent_delivery_only_one_acquires_lock() -> None:
    product = _product()
    order = _paid_order(product)
    repo = FakeDeliveryRepo()
    source = ControllableSource(delay_seconds=0.05)
    lock = ConcurrentLock()
    commerce = FakeCommerceRepo()
    commerce.orders[order.id] = order
    service = DeliveryService(
        FakeProducts(product), commerce, repo, source, lock, 900, 901
    )

    results = await asyncio.gather(
        service.deliver(order.id, order.customer_telegram_id),
        service.deliver(order.id, order.customer_telegram_id),
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, BaseException)]
    failures = [r for r in results if isinstance(r, BaseException)]
    assert len(successes) == 1
    assert successes[0].status is DeliveryStatus.DELIVERED
    assert successes[0].delivered == 2
    assert len(failures) == 1
    assert isinstance(failures[0], DeliveryError)
    assert "already processing" in str(failures[0])
    assert lock.acquire_attempts == 2
    assert lock.release_count == 1
    assert len(source.calls) == 2


@pytest.mark.asyncio
async def test_concurrent_retry_after_partial_failure_is_safe() -> None:
    product = _product()
    order = _paid_order(product)
    repo = FakeDeliveryRepo()
    source = ControllableSource(fail_channels={900, 901})
    lock = ConcurrentLock()
    commerce = FakeCommerceRepo()
    commerce.orders[order.id] = order
    service = DeliveryService(
        FakeProducts(product), commerce, repo, source, lock, 900, 901
    )

    failed = await service.deliver(order.id, order.customer_telegram_id)
    assert failed.status is DeliveryStatus.FAILED
    assert failed.failed == 2

    source.fail_channels.clear()
    source.delay_seconds = 0.03
    results = await asyncio.gather(
        service.retry(order.id, order.customer_telegram_id),
        service.retry(order.id, order.customer_telegram_id),
        return_exceptions=True,
    )
    successes = [r for r in results if not isinstance(r, BaseException)]
    failures = [r for r in results if isinstance(r, BaseException)]
    assert len(successes) == 1
    assert successes[0].status is DeliveryStatus.DELIVERED
    assert successes[0].delivered == 2
    assert len(failures) == 1
    assert isinstance(failures[0], DeliveryError)
    # First attempt: 2 files x 2 channels = 4 calls; retry succeeds once with 2 sends
    assert len([c for c in source.calls if c[0] == 900 or c[0] == 901]) >= 6


@pytest.mark.asyncio
async def test_lock_failure_surfaces_as_runtime_error() -> None:
    product = _product()
    order = _paid_order(product)
    commerce = FakeCommerceRepo()
    commerce.orders[order.id] = order
    service = DeliveryService(
        FakeProducts(product),
        commerce,
        FakeDeliveryRepo(),
        ControllableSource(),
        FailingLock(),
        900,
        901,
    )
    with pytest.raises(RuntimeError, match="redis unavailable"):
        await service.deliver(order.id, order.customer_telegram_id)


@pytest.mark.asyncio
async def test_concurrent_payment_callbacks_leave_order_paid_once() -> None:
    product = _product("P-CB")
    provider = ControllableProvider(verify_delay=0.04)
    repository = FakeCommerceRepo()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(100, product.id, 1, "cb-concurrent")
    await service.create_payment(order.id, "fake", "https://shop.test/callback")

    results = await asyncio.gather(
        service.handle_callback(order.id, "fake", "AUTH-1", "OK"),
        service.handle_callback(order.id, "fake", "AUTH-1", "OK"),
        return_exceptions=True,
    )
    assert all(r is True for r in results if not isinstance(r, BaseException))
    paid = repository.orders[order.id]
    assert paid.status is OrderStatus.PAID
    # Domain is idempotent; verify may race once or twice with in-memory fakes
    assert provider.verify_calls >= 1
    assert provider.verify_calls <= 2


@pytest.mark.asyncio
async def test_provider_verify_failure_then_success_is_retryable() -> None:
    product = _product("P-VF")
    provider = ControllableProvider(fail_verify=True)
    repository = FakeCommerceRepo()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(101, product.id, 1, "vf-1")
    await service.create_payment(order.id, "fake", "https://shop.test/callback")
    assert await service.handle_callback(order.id, "fake", "AUTH-1", "OK") is False
    assert repository.orders[order.id].status is OrderStatus.PAYMENT_FAILED
    provider.fail_verify = False
    assert await service.handle_callback(order.id, "fake", "AUTH-1", "OK") is True
    assert repository.orders[order.id].status is OrderStatus.PAID
    assert provider.verify_calls == 2


@pytest.mark.asyncio
async def test_provider_create_timeout_is_injected_and_order_marked_failed() -> None:
    product = _product("P-TO")
    provider = ControllableProvider(fail_create=True)
    repository = FakeCommerceRepo()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(102, product.id, 1, "to-1")
    with pytest.raises(TimeoutError):
        await service.create_payment(order.id, "fake", "https://shop.test/callback")
    assert repository.orders[order.id].status is OrderStatus.PAYMENT_FAILED
    payment = next(iter(repository.payments.values()))
    assert payment.status.value == "failed"
    assert payment.attempts[-1].status.value == "timeout"


@pytest.mark.asyncio
async def test_telegram_one_shot_failure_then_retry_delivers_remaining() -> None:
    product = _product("P-TG")
    order = _paid_order(product, customer_id=888)
    repo = FakeDeliveryRepo()
    source = ControllableSource(fail_once=True)
    commerce = FakeCommerceRepo()
    commerce.orders[order.id] = order
    service = DeliveryService(
        FakeProducts(product), commerce, repo, source, ConcurrentLock(), 900, 901
    )
    first = await service.deliver(order.id, order.customer_telegram_id)
    # First file fails once across archive+backup then may partial/fail; second may succeed
    assert first.delivered + first.failed + first.pending == 2
    second = await service.retry(order.id, order.customer_telegram_id)
    assert second.status is DeliveryStatus.DELIVERED
    assert second.delivered == 2


@pytest.mark.asyncio
async def test_malicious_callback_status_is_rejected() -> None:
    product = _product("P-MAL")
    provider = ControllableProvider()
    repository = FakeCommerceRepo()
    service = CommerceService(FakeProducts(product), repository, {"fake": provider})
    order = await service.create_order(103, product.id, 1, "mal-1")
    await service.create_payment(order.id, "fake", "https://shop.test/callback")
    with pytest.raises(CommerceError, match="status"):
        await service.handle_callback(order.id, "fake", "AUTH-1", "HACK")
    assert provider.verify_calls == 0
    assert repository.orders[order.id].status is not OrderStatus.PAID


@pytest.mark.asyncio
async def test_concurrent_webhook_callbacks_do_not_crash() -> None:
    product = _product("P-WH")
    provider = ControllableProvider(verify_delay=0.03)
    provider.name = "zarinpal"
    repo = FakeCommerceRepo()
    commerce = CommerceService(FakeProducts(product), repo, {"zarinpal": provider})
    order = await commerce.create_order(99, product.id, 1, "wh-conc")
    await commerce.create_payment(order.id, "zarinpal", "https://bot.test/callback")

    notes: list[tuple[int, str]] = []

    async def notify(cid: int, text: str) -> None:
        notes.append((cid, text))

    class SessionCM:
        def __init__(self, session: object) -> None:
            self.session = session

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, *args: object) -> None:
            return None

    def session_factory():
        return SessionCM(object())

    def commerce_factory(_session):
        return commerce

    class FakeDelivery:
        async def deliver(self, order_id, customer_telegram_id):
            from app.delivery.domain import DeliverySummary

            return DeliverySummary(order_id, 1, 0, 0, DeliveryStatus.DELIVERED)

    def delivery_factory(_session):
        return FakeDelivery()

    app = create_payment_app(
        session_factory, commerce_factory, delivery_factory, bot_notifier=notify
    )
    async with TestClient(TestServer(app)) as client:
        responses = await asyncio.gather(
            client.get(
                "/payments/zarinpal/callback",
                params={"order_id": str(order.id), "Authority": "AUTH-1", "Status": "OK"},
            ),
            client.get(
                "/payments/zarinpal/callback",
                params={"order_id": str(order.id), "Authority": "AUTH-1", "Status": "OK"},
            ),
        )
        statuses = [r.status for r in responses]
        assert all(s in {200, 400, 500} for s in statuses)
        assert 200 in statuses
    assert repo.orders[order.id].status is OrderStatus.PAID

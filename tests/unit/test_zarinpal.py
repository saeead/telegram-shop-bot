from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from app.application.commerce_ports import PaymentRequest, PaymentVerificationRequest
from app.payments.zarinpal import ZarinpalError, ZarinpalProvider


def make_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_zarinpal_request_validates_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/payment/request.json")
        return httpx.Response(
            200,
            json={"data": {"code": 100, "authority": "A-1", "message": "success"}},
        )

    provider = ZarinpalProvider("merchant", client=make_client(handler))
    result = await provider.create_payment(
        PaymentRequest(uuid4(), uuid4(), Decimal(1000), "IRR", "Order", "https://shop/callback", "k")
    )
    assert result.authority == "A-1"
    assert result.payment_url.endswith("/pg/StartPay/A-1")


@pytest.mark.asyncio
async def test_zarinpal_verify_accepts_success_and_already_verified():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"code": 101, "message": "Already Verified"}})

    provider = ZarinpalProvider("merchant", client=make_client(handler))
    result = await provider.verify_payment(
        PaymentVerificationRequest(uuid4(), uuid4(), "A-1", Decimal(1000), "IRR")
    )
    assert result.success is True
    assert result.already_verified is True
    assert result.provider_reference == "A-1"


@pytest.mark.asyncio
async def test_zarinpal_rejects_malformed_external_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"code": 100}})

    provider = ZarinpalProvider("merchant", client=make_client(handler))
    with pytest.raises(ZarinpalError, match="authority"):
        await provider.create_payment(
            PaymentRequest(uuid4(), uuid4(), Decimal(1000), "IRR", "Order", "https://shop/callback", "k")
        )


@pytest.mark.asyncio
async def test_zarinpal_provider_error_is_safe():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": {"code": -9, "message": "invalid"}})

    provider = ZarinpalProvider("merchant", client=make_client(handler))
    with pytest.raises(ZarinpalError, match="API error"):
        await provider.create_payment(
            PaymentRequest(uuid4(), uuid4(), Decimal(1000), "IRR", "Order", "https://shop/callback", "k")
        )

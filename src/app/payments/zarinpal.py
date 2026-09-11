"""ZarinPal REST API v4 adapter.

The provider is isolated behind PaymentProvider and returns validated domain-neutral
results. No ZarinPal types leak into the order domain.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx

from app.application.commerce_ports import (
    PaymentRequest,
    PaymentRequestResult,
    PaymentVerificationRequest,
    PaymentVerificationResult,
)
from app.domain.order import Payment


class ZarinpalError(RuntimeError):
    """Provider request/response validation failure."""


class ZarinpalProvider:
    name = "zarinpal"

    def __init__(
        self,
        merchant_id: str,
        sandbox: bool = False,
        timeout_seconds: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not merchant_id.strip():
            raise ValueError("merchant_id must not be empty")
        self._merchant_id = merchant_id.strip()
        self._sandbox = sandbox
        self._timeout = timeout_seconds
        self._client = client

    @property
    def base_url(self) -> str:
        return "https://sandbox.zarinpal.com" if self._sandbox else "https://api.zarinpal.com"

    async def create_payment(self, request: PaymentRequest) -> PaymentRequestResult:
        self._validate_amount_currency(request.amount, request.currency)
        payload = {
            "merchant_id": self._merchant_id,
            "amount": int(request.amount),
            "callback_url": request.callback_url,
            "description": request.description[:255],
            "metadata": {"order_id": str(request.order_id)},
        }
        response = await self._post("/pg/v4/payment/request.json", payload)
        data = self._validated_data(response)
        code = self._required_int(data, "code")
        authority = self._required_str(data, "authority")
        if code != 100:
            raise ZarinpalError(f"ZarinPal payment request rejected: {code}")
        payment_url = f"{self.base_url.replace('api.', '')}/pg/StartPay/{authority}"
        return PaymentRequestResult(
            provider=self.name,
            authority=authority,
            payment_url=payment_url,
            raw_metadata={"request_code": code, "message": self._optional_str(data, "message")},
        )

    async def verify_payment(
        self, request: PaymentVerificationRequest
    ) -> PaymentVerificationResult:
        if not request.authority.strip():
            raise ZarinpalError("authority must not be empty")
        self._validate_amount_currency(request.amount, request.currency)
        payload = {
            "merchant_id": self._merchant_id,
            "amount": int(request.amount),
            "authority": request.authority,
        }
        response = await self._post("/pg/v4/payment/verify.json", payload)
        data = self._validated_data(response)
        code = self._required_int(data, "code")
        if code not in {100, 101}:
            return PaymentVerificationResult(
                provider=self.name,
                success=False,
                provider_reference=None,
                already_verified=False,
                raw_metadata={"verify_code": code, "message": self._optional_str(data, "message")},
            )
        ref_id = (
            self._required_str(data, "ref_id")
            if code == 100
            else self._optional_str(data, "ref_id")
        )
        return PaymentVerificationResult(
            provider=self.name,
            success=True,
            provider_reference=ref_id or request.authority,
            already_verified=code == 101,
            raw_metadata={"verify_code": code, "message": self._optional_str(data, "message")},
        )

    async def refund(self, payment: Payment) -> str:
        raise NotImplementedError("ZarinPal refund is intentionally deferred from Phase 4")

    async def _post(self, path: str, payload: dict[str, object]) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.post(f"{self.base_url}{path}", json=payload)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ZarinpalError("invalid or unavailable ZarinPal response") from exc
        finally:
            if own_client:
                await client.aclose()
        if not isinstance(body, dict):
            raise ZarinpalError("ZarinPal response must be an object")
        return body

    @staticmethod
    def _validate_amount_currency(amount: Decimal, currency: str) -> None:
        if amount <= 0 or amount != amount.to_integral_value():
            raise ZarinpalError("payment amount must be a positive whole number")
        if currency.upper() != "IRR":
            raise ZarinpalError("ZarinPal payments require IRR")

    @staticmethod
    def _validated_data(body: dict[str, Any]) -> dict[str, Any]:
        errors = body.get("errors")
        if errors not in (None, {}, []):
            if not isinstance(errors, dict):
                raise ZarinpalError("invalid ZarinPal errors payload")
            raise ZarinpalError(f"ZarinPal API error: {errors.get('code', 'unknown')}")
        data = body.get("data")
        if not isinstance(data, dict):
            raise ZarinpalError("ZarinPal response data is invalid")
        return data

    @staticmethod
    def _required_str(data: dict[str, Any], key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ZarinpalError(f"ZarinPal response missing valid {key}")
        return value.strip()

    @staticmethod
    def _optional_str(data: dict[str, Any], key: str) -> str | None:
        value = data.get(key)
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _required_int(data: dict[str, Any], key: str) -> int:
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise ZarinpalError(f"ZarinPal response missing valid {key}")
        try:
            return int(value)
        except ValueError as exc:
            raise ZarinpalError(f"ZarinPal response has invalid {key}") from exc

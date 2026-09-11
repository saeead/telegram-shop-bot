"""Future crypto payment provider boundary; no provider is selected in Phase 4."""

from __future__ import annotations

from typing import Protocol

from app.application.commerce_ports import PaymentProvider


class CryptoPaymentProvider(PaymentProvider, Protocol):
    """Marker boundary for a future crypto provider implementation.

    The Order and Payment domains depend only on PaymentProvider. A concrete crypto
    gateway can implement this protocol later without changing commerce entities.
    """

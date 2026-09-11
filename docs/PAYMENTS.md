# Payments

Payment is provider-agnostic.

Initial fiat provider: Zarinpal, subject to final API contract verification in the payment phase.

Crypto: provider selection is intentionally deferred. The domain/application layer exposes a provider contract so a concrete crypto gateway can be added without changing order logic.

Required payment properties:
- explicit amount/currency
- order binding
- provider reference
- idempotency key
- callback validation
- replay protection
- success/failure/expired/cancelled states
- audit trail

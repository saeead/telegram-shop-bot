# PROGRESS

## Current Verified State
- Phase: 4 — Orders & Payment — implementation in progress; final verification pending.
- Repository state: `phase-4-orders-payment` branches from the verified Phase 3 head `b1ab44842442ea7eb29c3364ff170a04b43343d3`.
- Phase 3 verification evidence: GitHub Actions CI run `34638030154` completed successfully.
- Standard verification gate: `pytest`, `ruff check .`, `ruff format --check .`, `mypy src`, `python -m compileall -q src`, Alembic upgrade, and `./scripts/check.sh`.
- Phase 4 must remain open for manual review; no merge is automatic.
- Delivery logic is intentionally excluded from Phase 4.

## Phase status
| Phase | Status | Exit condition |
|---|---|---|
| 1 Foundation & Harness | passing | FND-001..FND-004 passing with reproducible evidence |
| 2 Product & Telegram Intake | passing | admin can intake, classify, collect metadata, confirm, publish boundary |
| 3 Store & Admin | passing | store browsing/admin management works and full verification passes |
| 4 Orders & Payment | in_progress | order lifecycle, price snapshots, idempotent payments, Zarinpal verification, callback security, and full checks pass |
| 5 Delivery & Commerce | not_started | paid multi-file delivery is reliable and auditable |
| 6 Hardening & Scale | not_started | security, observability, recovery, webhooks, production readiness |

## Phase 4 implementation record
### PAY-001 — Orders and Zarinpal
- Added pure `Order`, `OrderItem`, `Payment`, and `PaymentAttempt` domain models.
- Added explicit order lifecycle: pending payment, processing, paid, failed, cancelled, expired.
- Order items snapshot product name, unit price, currency, and quantity at order creation.
- Added order and payment idempotency keys and provider-reference uniqueness boundaries.
- Added provider-agnostic `PaymentProvider` port with create, verify, and refund operations.
- Added `CommerceService` for order creation, payment creation, callback verification, replay protection, and expiry handling.
- Added real Zarinpal REST v4 request/verify adapter with strict response validation and safe metadata.
- Added untrusted Zarinpal callback parsing and validation.
- No delivery invocation exists in payment handling.

### PAY-002 — Crypto abstraction
- Added `CryptoPaymentProvider` abstraction over the generic provider port.
- No concrete crypto gateway was selected or coupled to the Order domain.

### Persistence
- Added Alembic migration `0004_orders_payment`.
- Added PostgreSQL persistence models for orders, order items, payments, and payment attempts.
- Payment attempts retain provider, provider reference, amount, status, timestamps, and safe metadata; no credentials are persisted.

### Tests
- Added order lifecycle and expiry tests.
- Added fake-provider tests for successful payment, failed payment, duplicate callbacks, invalid callbacks, amount mismatch, provider timeout, provider retry, already-paid order, and idempotent order/payment creation.
- Added Zarinpal adapter response-validation tests.
- Added callback parser security tests.

## Phase gate
Phase 4 remains `in_progress`. Do not start Phase 5 until the final CI verification is green and PAY-001 has executable evidence.

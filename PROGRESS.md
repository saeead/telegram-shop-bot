# PROGRESS

## Current Verified State
- Phase: 5 — Delivery & Commerce — implementation in progress.
- Phase 4 — Orders & Payment is verified and passing.
- Phase 4 CI evidence: GitHub Actions CI run `34710336327` completed successfully on commit `9d4ae51fc1940d9cf8d2ff14c40978c8289970c0`.
- Standard verification gate: `pytest`, `ruff check .`, `ruff format --check .`, `mypy src`, `python -m compileall -q src`, Alembic upgrade, and `./scripts/check.sh`.
- Phase 5 must remain open for manual review; no merge is automatic.
- Phase 6 must not start until the complete Admin → Store → Buy → Order → Payment → Verification → Delivery flow is end-to-end verified.

## Phase status
| Phase | Status | Exit condition |
|---|---|---|
| 1 Foundation & Harness | passing | FND-001..FND-004 passing with reproducible evidence |
| 2 Product & Telegram Intake | passing | admin can intake, classify, collect metadata, confirm, publish boundary |
| 3 Store & Admin | passing | store browsing/admin management works and full verification passes |
| 4 Orders & Payment | passing | order lifecycle, price snapshots, idempotent payments, Zarinpal verification, callback security, and full checks pass |
| 5 Delivery & Commerce | in_progress | paid multi-file delivery is reliable, secure, retryable, auditable, and E2E verified |
| 6 Hardening & Scale | not_started | security, observability, recovery, webhooks, production readiness |

## Phase 4 verified implementation record
- Order, OrderItem, Payment, and PaymentAttempt domain models with explicit lifecycle states.
- Price snapshots, order/payment idempotency, provider-reference uniqueness, and replay protection.
- Provider-agnostic PaymentProvider port and CryptoPaymentProvider abstraction.
- Zarinpal REST v4 request/verify adapter with strict response validation.
- Untrusted callback validation and payment-attempt ledger persistence.
- No delivery logic in payment handlers.

## Phase 5 scope
### Delivery
- Independent Delivery service and application port; no delivery implementation inside payment providers or Telegram handlers.
- Private Telegram Archive and Backup source channels are the delivery source of main files.
- Deterministic multi-file lookup and delivery ordering.
- Per-file delivery tracking with order/product/file/message/status/attempt/error/timestamp data.
- Delivery states: `PENDING`, `PROCESSING`, `PARTIAL`, `DELIVERED`, `FAILED`.
- Idempotent retry and recovery after Telegram timeout, deleted source messages, unavailable backup, partial delivery, bot restart, Redis restart, duplicate payment callback, and duplicate delivery request.

### Customer access
- Delivery is permitted only for successfully paid orders owned by the requesting customer.
- Customer cannot use another customer's order ID or product code to obtain files.
- Customer history includes My Orders, order details, purchased products, and retry delivery.

### Verification
- Fake Telegram/source-channel adapters for deterministic tests.
- Security/replay tests for forged product codes, foreign order IDs, unpaid orders, and duplicate delivery requests.
- Mandatory full E2E test: Admin creates Product → publishes → Customer buys → Order → Payment → Verification → Delivery of all main files.

## Phase gate
Phase 5 remains `in_progress`. Do not mark passing or start Phase 6 until the complete delivery recovery/security test suite and the full end-to-end flow are green with executable evidence.

# Session Handoff

## Where we are
Phase 3 — Store & Admin is verified and passing. Phase 4 — Orders & Payment is active on `phase-4-orders-payment`, branched from verified Phase 3 head `b1ab44842442ea7eb29c3364ff170a04b43343d3`.

## Verified Phase 3 evidence
- GitHub Actions CI run: `34638030154`
- Phase 3 head: `b1ab44842442ea7eb29c3364ff170a04b43343d3`
- CI completed successfully with the repository verification workflow.

## Phase 4 implemented scope
- Pure Order, OrderItem, Payment, and PaymentAttempt domain models.
- Explicit order lifecycle with payment processing, paid, failed, cancelled, and expired states.
- Price snapshots in OrderItem so Product price changes cannot alter historical orders.
- Order and payment idempotency boundaries.
- Provider-agnostic PaymentProvider port with create, verify, and refund.
- Commerce application service for order creation, payment creation, callback verification, expiry, replay protection, and failure handling.
- Real Zarinpal REST API v4 request/verify adapter with response validation.
- Untrusted callback parsing and checks for order, provider, authority, amount, state, and replay.
- Payment attempt ledger persistence with safe metadata only.
- CryptoPaymentProvider abstraction; concrete provider deliberately deferred.
- Alembic migration `0004_orders_payment`.
- Fake-provider, Zarinpal adapter, callback parser, lifecycle, and persistence-oriented unit coverage.

## Phase 4 constraints
- Payment credentials, merchant secrets, card data, and sensitive payment data must never be stored.
- Browser/provider callback is never treated as proof of payment; provider verification is required.
- Already-paid orders are terminal and repeated callbacks must not trigger another verification or payment transition.
- No Delivery/fulfillment logic is allowed in Phase 4 payment handlers.
- Domain code must remain independent of aiogram, SQLAlchemy, Redis, and payment SDKs.
- No concrete crypto provider is selected in this phase.

## Verification gate
Before Phase 4 can be marked passing:
- `pytest`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- `python -m compileall -q src`
- Alembic/PostgreSQL integration via CI.
- Verify fake-provider success/failure, duplicate callback, invalid callback, amount mismatch, expiry, provider timeout/retry, and already-paid behavior.
- Verify Zarinpal external response validation.

## Current state
- Phase 4 is `in_progress` until final CI is green.
- PAY-001 remains the active feature; PAY-002 crypto abstraction is implemented but no production provider is selected.
- PR for Phase 4 must remain open for manual approval and must not be merged automatically.

## Next action
Run the Phase 4 CI verification. Fix every failure directly on `phase-4-orders-payment`. Only after the complete verification gate is green should PAY-001 be marked passing and Phase 4 closed. Do not start Phase 5 until then.

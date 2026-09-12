# PROGRESS

## Current Verified State
- Phase: 5 — Delivery & Commerce — verified and passing.
- Phase 4 — Orders & Payment is verified and passing.
- Phase 5 CI evidence: GitHub Actions run `34711911244` completed successfully on commit `abde684c01174535fe7b0fd17d52a10d6a211b7a`.
- Phase 5 verification: 56 tests passed, Alembic upgraded through `0005_delivery`, Ruff check/format passed, mypy passed, compileall passed, and the full purchase → payment verification → multi-file delivery E2E passed.
- Standard verification gate: `pytest`, `ruff check .`, `ruff format --check .`, `mypy src`, `python -m compileall -q src`, Alembic upgrade, and `./scripts/check.sh`.
- Phase 5 implementation is on branch `phase-5-delivery-commerce`; PR #7 is open for manual review/merge. No merge is automatic.
- Phase 6 may start from the verified Phase 5 head, but production-ready status must remain unclaimed until Phase 6 Definition of Done is satisfied.

## Phase status
| Phase | Status | Exit condition |
|---|---|---|
| 1 Foundation & Harness | passing | FND-001..FND-004 passing with reproducible evidence |
| 2 Product & Telegram Intake | passing | admin can intake, classify, collect metadata, confirm, publish boundary |
| 3 Store & Admin | passing | store browsing/admin management works and full verification passes |
| 4 Orders & Payment | passing | order lifecycle, price snapshots, idempotent payments, Zarinpal verification, callback security, and full checks pass |
| 5 Delivery & Commerce | passing | paid multi-file delivery is reliable, secure, retryable, auditable, and E2E verified |
| 6 Hardening & Scale | not_started | security, observability, recovery, webhooks, production readiness |

## Phase 5 verified implementation record
- Independent `DeliveryService` with repository/source/lock ports; payment providers and Telegram handlers do not own delivery business logic.
- Private Archive/Backup source channel configuration with deterministic fallback through the Telegram copy-message adapter.
- Main-file-only delivery ordered deterministically by product-file ordering and stable file ID.
- Per-order/per-file delivery persistence with unique constraint, status, attempt count, destination Telegram message ID, delivered timestamp, and safe last-error text.
- Delivery states: `PENDING`, `PROCESSING`, `PARTIAL`, `DELIVERED`, `FAILED`.
- Retry is idempotent after a successful persisted delivery; already-delivered files are skipped.
- Customer authorization requires a paid order owned by the requesting Telegram user.
- Product-code authorization is constrained to products actually contained in the customer's paid order.
- Customer history/details/retry service boundaries are available through the Delivery service and Commerce repository.
- Telegram API failures are converted to a safe delivery-source error without exposing raw provider exceptions to business state.
- Alembic migration `0005_delivery` adds persistent delivery tracking and uniqueness constraints.
- Unit tests cover multi-file ordering, duplicate retry, Archive→Backup fallback, partial failure/recovery, foreign-order rejection, unpaid-order rejection, product-code authorization, and duplicate-request locking.
- Integration E2E covers Product → Order → Payment → Verification → Delivery and verifies all main files are delivered.

## Phase 5 evidence
- CI run: `34711911244`
- Verified commit: `abde684c01174535fe7b0fd17d52a10d6a211b7a`
- Test result: `56 passed`
- Migration result: `0005_delivery` applied successfully
- Formatting/lint/type/compile result: all passed through `scripts/check.sh`
- E2E result: full purchase → payment verification → multi-file delivery passed

## Phase gate
Phase 5 is `passing` based on executable evidence above. Phase 6 is now the only development feature that may become `in_progress`; do not claim production-ready status until Phase 6 is independently implemented, tested, verified, and documented.

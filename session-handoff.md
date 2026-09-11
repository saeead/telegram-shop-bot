# Session Handoff

## Where we are
Phase 1 — Foundation & Harness.

## Active feature state
No feature is `in_progress`; FND-001..FND-004 are implemented but `blocked` pending executable verification in an environment with Python package-index access and PostgreSQL/Redis services.

## What changed
- Kept the existing Pydantic Settings and bootstrap foundation.
- Added SQLAlchemy 2.x async engine/session factory and database health check.
- Added async Alembic environment and an empty baseline migration; no business tables were introduced.
- Aligned Docker PostgreSQL database name with `DATABASE_URL`.
- Added application `CachePort` and Redis adapter for transient state, TTL cache, locks, and idempotency storage.
- Added PostgreSQL/Redis integration health tests.
- Extended `scripts/check.sh` with compile verification.
- Added GitHub Actions CI with PostgreSQL and Redis services and migration execution.
- Updated repository progress/feature evidence without falsely marking unverified work as passing.

## Verification status
- Previous scaffold evidence: `pytest -q` → 3 passed; `python -m compileall -q src` → passed.
- Current Phase 1 changes: not locally executed because this environment cannot reach the external Python package index and does not provide Docker.
- CI workflow is present but must complete successfully before feature statuses can be changed to `passing`.

## Important truth
Do not mark any Phase 1 feature as passing without fresh executable evidence covering the completed branch.

## Next action
1. Open the Phase 1 PR and let CI execute with PostgreSQL and Redis services.
2. If CI passes, rerun the exact verification commands in a developer environment and record the evidence.
3. Only after FND-001..FND-004 are all `passing`, begin Phase 2.

## Do not do yet
- No product intake.
- No Product/Order/Payment/Customer business tables.
- No Telegram product handlers.
- No payment implementation.
- No delivery implementation.
- No WooCommerce integration.

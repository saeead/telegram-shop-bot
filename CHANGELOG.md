# Changelog

## Unreleased — Phase 1 Foundation

- Added async PostgreSQL engine, session factory, and health check.
- Added async Alembic migration infrastructure with an empty foundation revision.
- Aligned Docker PostgreSQL database name with application settings.
- Added Redis cache/state adapter with TTL, lock, and idempotency primitives behind an application port.
- Added PostgreSQL and Redis integration health tests.
- Extended the standard verification harness with source compilation checks.
- Added GitHub Actions CI with PostgreSQL and Redis service containers.
- Kept Phase 1 feature states blocked until fresh executable verification is available.

No store, product, payment, or delivery features were implemented in this phase.

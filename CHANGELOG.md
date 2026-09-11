# Changelog

## Unreleased — Phase 1 Foundation

- Added async PostgreSQL engine, session factory, and health check.
- Added async Alembic migration infrastructure with an empty foundation revision.
- Aligned Docker PostgreSQL database name with application settings.
- Added Redis cache/state adapter with TTL, lock, and idempotency primitives behind an application port.
- Added PostgreSQL and Redis integration health tests.
- Extended the standard verification harness with source compilation checks.
- Added GitHub Actions CI with PostgreSQL and Redis service containers.
- Fixed environment-isolated settings tests, Redis typing, and narrow exception handling for strict lint/type checks.
- Verified Phase 1 through GitHub Actions CI run `34632397963` with PostgreSQL/Redis services, Alembic migration, and the standard verification harness.
- Marked FND-001..FND-004 as `passing` with executable evidence.

No store, product, payment, or delivery features were implemented in Phase 1.

# Changelog

## Unreleased — Phase 3 Store & Admin

- Added public Store caption/presentation helpers outside the Product domain.
- Added Telegram Store publisher adapter that publishes preview media only and never main product files.
- Added Buy CTA callback boundary without implementing payment.
- Added versioned and safely encoded callback data validation.
- Added Home, Categories, Tags, Products, category filtering, and tag filtering navigation.
- Added HIDDEN product status and hide/republish lifecycle.
- Added StorePublication persistence with idempotent duplicate-publication prevention.
- Added explicit server-side admin authorization.
- Added Admin product editing for name, price, category, and tags, plus hide, republish, and details actions.
- Added AuditLog persistence for actor, action, entity, entity_id, timestamp, and metadata.
- Added Alembic migration `0003_store_admin`.
- Added Store/Admin unit tests and PostgreSQL persistence integration coverage.
- Phase 3 verification remains pending; do not mark Phase 3 passing until the final CI gate is green.

## Unreleased — Phase 2 Product Intake & Domain

- Added Product aggregate and ProductFile/ProductPreview domain concepts.
- Added Category, Tag, ProductStatus, and ProductIntake state machine.
- Added Telegram file classification for preview and main roles.
- Added product-code generation and metadata validation.
- Added admin metadata review, confirmation, edit, cancellation, and publication boundary orchestration.
- Added PostgreSQL product/intake persistence and Alembic migration `0002_product_intake`.
- Added Redis transient intake state integration.
- Added Telegram adapter boundary and fake/test coverage.
- Added unit and integration tests for Product, classification, intake transitions, persistence, Redis, and Telegram boundaries.
- Fixed Phase 2 Ruff formatting and verified the final branch through CI.
- Verified Phase 2 with GitHub Actions CI run `34634205262`: 19 tests passed, Alembic succeeded, Ruff formatting/lint passed, mypy passed, and harness validation passed.

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

No payment or delivery features are included in Phase 2 or Phase 3.

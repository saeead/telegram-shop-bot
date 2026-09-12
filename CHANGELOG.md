# Changelog

## Unreleased — Phase 4 Orders & Payment

- Added pure Order, OrderItem, Payment, and PaymentAttempt domain models with explicit lifecycle states.
- Added price snapshots at order creation so later Product price changes do not mutate historical orders.
- Added idempotent order creation and payment creation boundaries.
- Added PaymentProvider abstraction for create, verify, and refund operations.
- Added ZarinPal REST API v4 request and verification adapter with strict external-response validation.
- Added untrusted ZarinPal callback parser and replay/amount/provider/authority validation in the commerce service.
- Added PostgreSQL persistence for orders, order items, payments, and payment attempts.
- Added safe payment-attempt metadata storage without payment credentials or secrets.
- Added explicit expiry and payment failure handling, including provider timeout handling.
- Added a crypto provider abstraction without selecting a concrete crypto gateway.
- Added fake-provider tests for successful/failed payment, duplicate callback, invalid callback, amount mismatch, expiry, timeout, retry, already-paid order, and idempotency.
- Added ZarinPal adapter response-validation tests.
- Added Alembic migration `0004_orders_payment`.
- Delivery logic remains intentionally out of scope for Phase 4.

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
- Verified Phase 3 through GitHub Actions CI run `34638030154` on head `b1ab44842442ea7eb29c3364ff170a04b43343d3`.

## Unreleased — Phase 2 Product Intake & Domain

- Added Product aggregate and ProductFile/ProductPreview domain concepts.
- Added Category, Tag, ProductStatus, and ProductIntake state machine.
- Added Telegram file classification for preview and main roles.
- Added product-code generation and metadata validation.
- Added admin metadata review, confirmation, edit, cancellation, and publication boundary orchestration.
- Added PostgreSQL product/intake persistence and Alembic migration `0002_product_intake`.
- Added Redis transient intake state integration.
- Added Telegram adapter boundary and fake/test coverage.
- Verified Phase 2 with GitHub Actions CI run `34634205262`.

## Unreleased — Phase 1 Foundation

- Added async PostgreSQL engine, session factory, and health check.
- Added async Alembic migration infrastructure with an empty foundation revision.
- Added Redis cache/state adapter with TTL, lock, and idempotency primitives behind an application port.
- Added PostgreSQL and Redis integration health tests.
- Added standard verification harness and GitHub Actions CI with PostgreSQL and Redis services.
- Verified Phase 1 through GitHub Actions CI run `34632397963`.

No Delivery implementation is included in Phase 4.

# PROGRESS

## Current Verified State
- Phase: 3 — Store & Admin — implementation in progress; verification pending.
- Repository state: `phase-3-store-admin` is open in PR #3 against the verified Phase 2 branch `phase-2-product-intake`.
- Phase 2 remains verified and passing with CI run `34634205262`.
- Current Phase 3 verification run is pending after the latest implementation commits.
- Highest priority active feature: `STR-001`.
- Production readiness: not applicable.

## Phase status
| Phase | Status | Exit condition |
|---|---|---|
| 1 Foundation & Harness | passing | FND-001..FND-004 passing with reproducible evidence |
| 2 Product & Telegram Intake | passing | admin can intake, classify, collect metadata, confirm, publish boundary |
| 3 Store & Admin | in_progress | store browsing/search/admin management works and full verification passes |
| 4 Orders & Payment | not_started | IRR + crypto abstraction and idempotent payment flow |
| 5 Delivery & Commerce | not_started | paid multi-file delivery is reliable and auditable |
| 6 Hardening & Scale | not_started | security, observability, recovery, webhooks, production readiness |

## Phase 2 completion evidence
### PRD-001 — Product intake and file classification
- Product aggregate, ProductFile, ProductPreview, Category, Tag, ProductStatus, and ProductIntake implemented.
- Telegram batches are classified into previews and main files without storing file bytes on the application server.
- Product codes are generated and persisted with Telegram file/message/chat references.
- Status: `passing`.
- Evidence: CI run `34634205262` passed with PostgreSQL and Redis services.

### PRD-002 — Admin metadata collection and confirmation
- Intake FSM implements receiving, classification, metadata collection, admin confirmation, publishing boundary, published, failed, and cancelled states.
- Metadata validation, review summary, Confirm/Edit/Cancel flow, PostgreSQL persistence, Redis transient state, and Telegram adapter boundary are covered by tests.
- Status: `passing`.
- Evidence: CI run `34634205262` passed; `scripts/check.sh` reported 19 passed, Ruff formatting/lint passed, mypy passed, migrations passed, and harness validation passed.

## Phase 3 implementation record
### STR-001 — Public Store
- Added public Store caption/presentation helpers outside the domain.
- Added Telegram Store publisher boundary/adapter that publishes preview media only and never main downloadable files.
- Added versioned callback encoding/validation with safe value encoding.
- Added Home, Categories, Tags, Products, category filtering, tag filtering, and Buy callback boundary.
- Added Store publication persistence and idempotent publication lookup.

### STR-002 — Admin Store
- Added explicit server-side AdminAuthorizer.
- Added product edit operations for name, price, category, and tags.
- Added Hide, Republish, and View Details operations.
- Added HIDDEN product status while preserving historical records.
- Added audit log persistence with actor/action/entity/entity_id/timestamp/metadata.
- Added admin menu for Products, Categories, Orders, and Settings; payment/order processing remains out of scope.

### Persistence and tests
- Added Alembic migration `0003_store_admin` for StorePublication and AuditLog persistence.
- Added PostgreSQL integration coverage for Store publication/audit persistence.
- Added unit coverage for publication idempotency, authorization, edits, hide/republish lifecycle, callback validation, and preview-only presentation.

## Session records
### Session 005 — Phase 3 Store & Admin implementation
- Created `phase-3-store-admin` from the verified Phase 2 state.
- Opened PR #3 against `phase-2-product-intake`; PR #3 must remain open for manual approval.
- Implemented the Phase 3 Store/Admin scope without Payment or Delivery.
- One early CI run failed only because the new Store service test fixtures omitted required ProductFile metadata; the fixture was corrected.
- Latest verification is pending and Phase 3 must not be marked passing until fresh CI evidence is green.

## Phase gate
Phase 3 remains `in_progress`. Do not start Phase 4 until `pytest`, `ruff check .`, `ruff format --check .`, `mypy src`, migrations/integration checks, and the Store/Admin tests all pass on the final head.

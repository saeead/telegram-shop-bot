# Session Handoff

## Where we are
Phase 2 — Product Intake & Domain is verified and passing. Phase 3 — Store & Admin is active on `phase-3-store-admin` in PR #3, targeting the verified Phase 2 branch `phase-2-product-intake`.

## Verified Phase 2 evidence
- GitHub Actions CI run: `34634205262`
- PR #2 merge commit verified: `688e3eebccbaa16ee3b3a22c519b11ad69714a7c`
- Phase 2 head commit verified: `23db38397da7f043eb3b64d8a156abf885ba45ef`
- `scripts/check.sh`: 19 tests passed, formatting passed, mypy passed, and harness validation passed.
- PostgreSQL and Redis service containers were healthy and Alembic upgraded successfully.

## Phase 2 completed scope
- Product aggregate and ProductFile/ProductPreview/Category/Tag/ProductStatus/ProductIntake.
- File classification and product code generation.
- Intake FSM, metadata validation, admin review, confirmation, edit/cancel boundary.
- PostgreSQL persistence and Redis transient intake state.
- Telegram adapter boundary and tests.
- No payment or delivery implementation.

## Phase 3 implemented scope
- Public Store presentation and caption generation outside the domain.
- Preview-only Telegram media-group publication and Buy CTA boundary.
- Versioned, encoded, validated callback data.
- Home, Categories, Tags, Products, category filtering, and tag filtering.
- StorePublication persistence and idempotent publication prevention.
- Explicit server-side admin authorization.
- Admin product listing/details and editing for name, price, category, and tags.
- Hide and republish with historical records retained.
- AuditLog persistence for important admin actions.
- Alembic migration `0003_store_admin`.
- Unit and PostgreSQL integration coverage.

## Phase 3 constraints
- Payment is out of scope.
- Zarinpal and crypto SDKs are out of scope.
- Delivery/fulfillment is out of scope.
- Main product files must never be published in the public Store channel.
- Domain must not import aiogram, Telegram Bot API, SQLAlchemy, Redis, payment SDKs, or delivery SDKs.
- Presentation/caption logic belongs outside the domain.
- Admin authorization must be explicit and cannot rely on client-supplied callback data.

## Verification gate
Before Phase 3 can be marked passing:
- `pytest`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- PostgreSQL integration and Alembic migration.
- Redis integration where relevant.
- Telegram adapter boundary tests.
- Verify no main files are exposed through public publication code.
- Verify publication idempotency, callback validation, authorization, and audit records.

## Current state
- Phase 3 remains `in_progress` until fresh CI is green.
- An early CI run exposed incomplete ProductFile metadata in a new test fixture; that fixture was corrected.
- Latest implementation also added full admin edit controls and public tag navigation.
- PR #3 remains open and must not be merged automatically.

## Next action
Wait for and inspect the final CI run on the latest head. Fix any remaining verification failures. Only after a green verification gate should `STR-001`/`STR-002` be marked passing and Phase 3 closed. Do not start Phase 4 until then.

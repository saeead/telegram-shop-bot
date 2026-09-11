# Session Handoff

## Where we are
Phase 2 — Product Intake & Domain is verified and passing. Phase 3 — Store & Admin is now active on `phase-2-product-intake` and must be implemented without payment or delivery.

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

## Phase 3 scope
- Public Telegram Store presentation of published products using preview media only.
- Product caption builder outside the domain layer.
- Multi-preview/media-group publication where supported.
- Category navigation and tag filtering.
- Customer Home/Categories/Products/Search/Back navigation.
- Versioned and validated callback data.
- Explicit admin authorization on every admin command and callback.
- Admin menu for Products, Categories, Orders placeholder/navigation, and Settings placeholder/navigation as appropriate without implementing payment/order processing.
- Product editing: price, name, category, tags; hide; republish; details.
- Product visibility states including HIDDEN while preserving historical DB records.
- Idempotent publication/republish prevention.
- Audit log with actor, action, entity, entity_id, timestamp, metadata.
- Tests for navigation, filtering, publication, hide, republish, edits, authorization, callback validation, and duplicate publication prevention.

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
- PostgreSQL integration where relevant.
- Redis integration where relevant.
- Telegram adapter boundary tests.
- Verify no main files are exposed through public publication code.
- Verify publication idempotency and audit records.

## Next action
Create `phase-3-store-admin` from the verified Phase 2 state, implement Phase 3 features, update `feature_list.json`, `PROGRESS.md`, `CHANGELOG.md`, `DECISIONS.md`, and this handoff, then run the full verification gate. Do not start Phase 4 until Phase 3 is verified.

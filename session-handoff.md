# Session Handoff

## Where we are
Phase 1 — Foundation & Harness is verified and passing. Phase 2 — Product Intake & Domain is authorized and in progress.

## Active feature state
`PRD-001` is `in_progress`. All other features remain `not_started` unless already marked `passing` in `feature_list.json`.

## Phase 1 verification evidence
- GitHub Actions CI run: `34632397963`
- Verified commit before documentation closeout: `61544abfac695081c272c584656f4bfa252ef5f2`
- CI verify job completed successfully.
- The verify job installed dependencies, ran `alembic upgrade head`, and ran `scripts/check.sh` with PostgreSQL and Redis service containers.
- FND-001..FND-004 are recorded as `passing` in `feature_list.json`.

## Phase 2 scope
- Build Product aggregate and related domain concepts.
- Implement ProductFile/ProductPreview/Category/Tag/ProductStatus/ProductIntake concepts.
- Implement explicit intake state machine with valid transitions and failure states.
- Implement classification of Telegram-forwarded media/files without storing file bytes on the application server.
- Implement product-code generation and metadata validation.
- Implement application orchestration for admin intake, metadata collection, review, confirmation, edit, and cancellation.
- Implement Telegram adapter boundary and fake adapter tests where practical.
- Add PostgreSQL persistence for Phase 2 business data only.
- Use Redis only through the existing application port/abstraction for FSM/transient intake state.

## Explicitly out of scope
- Customer purchase flow.
- Payment/Zarinpal/crypto integration.
- Delivery/fulfillment.
- Store publication UX beyond the Phase 2 confirmation/publishing boundary needed by the intake use case.
- WooCommerce/webhook integration.

## Required architecture
`presentation/telegram -> application -> domain`
`infrastructure -> application/domain`
`domain -> nothing external`

Domain must not import aiogram, Telegram Bot API, SQLAlchemy, Redis, Zarinpal, or crypto SDKs.

## Required verification before Phase 2 completion
- `pytest`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- Integration coverage for persistence, intake state, Redis FSM, and Telegram adapter boundary.
- Record executable evidence in `feature_list.json` and `PROGRESS.md`.

## Next action
Implement `PRD-001` first, with small testable changes. Then implement `PRD-002`. Keep exactly one feature `in_progress`. Do not start Phase 3 until Phase 2 is verified.

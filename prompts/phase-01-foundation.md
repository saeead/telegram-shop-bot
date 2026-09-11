# Phase 01 — Foundation & Harness

## Mission
Finish and verify the repository foundation. Do not implement catalog, store, payment, delivery, or website features in this phase.

## Mandatory reading
Read, in this order:
1. `AGENTS.md`
2. `README.md`
3. `PROGRESS.md`
4. `feature_list.json`
5. `DECISIONS.md`
6. `docs/ARCHITECTURE.md`
7. `docs/CONSTRAINTS.md`
8. `docs/TESTING.md`
9. `session-handoff.md`

## Current repository truth
The repository already contains the Harness scaffold and a minimal validated configuration/bootstrap implementation.
The current active feature is `FND-001`.
Do not assume any database, Redis, Telegram, or payment integration is complete.

## Work order
Execute features strictly in this order:

### FND-001 — Runnable application and configuration
- Verify Python/package metadata.
- Verify environment configuration validation.
- Verify missing `TELEGRAM_BOT_TOKEN` fails clearly.
- Verify application startup with a test token.
- Verify `pytest`.
- If the environment has network access, verify `./init.sh` from a clean environment.
- If dependency installation is blocked by the execution environment, record the exact blocker as environment evidence; do not fake a passing result.

### FND-002 — PostgreSQL and migrations
Only start after FND-001 has passing evidence.
- Add SQLAlchemy 2.x async engine/session infrastructure.
- Add Alembic configuration.
- Add a minimal health/check migration.
- Keep domain code free from SQLAlchemy imports.
- Add integration tests using the configured PostgreSQL service.
- Never introduce product business tables before the domain model phase requires them.

### FND-003 — Redis state infrastructure
Only start after FND-002 has passing evidence.
- Add a Redis adapter behind an application port/interface.
- Provide connectivity and clean-restart tests.
- Keep Redis-specific code out of domain entities.
- Establish primitives required later for FSM state, locks, idempotency, and cache.

### FND-004 — Standard verification and clean-state checks
Only start after FND-003 has passing evidence.
- Make `scripts/check.sh` the standard repository verification command.
- Validate `feature_list.json` invariants.
- Add a machine-checkable clean-state checklist.
- Ensure a fresh agent can determine current phase, active feature, verification status, blockers, and next action.

## Architectural constraints
- Python 3.12+.
- aiogram 3.x, but no Telegram business logic in Phase 1.
- PostgreSQL via SQLAlchemy 2.x + asyncpg.
- Alembic for migrations.
- Redis for transient state/locks.
- Pydantic Settings for configuration.
- Structured application logging.
- Domain layer must not import framework/infrastructure dependencies.
- Product files must not be stored on the application filesystem as part of normal operation.
- Secrets must never be committed.
- One feature may be `in_progress` at a time.
- Never mark a feature `passing` without executable evidence.

## Required verification loop
For every feature:
1. State the feature ID.
2. Inspect affected files before editing.
3. Make the smallest coherent change.
4. Add/update tests.
5. Run targeted tests.
6. Run the broader repository check when the feature is ready.
7. Record exact commands and results in `PROGRESS.md`.
8. Update `feature_list.json` only from verified evidence.
9. Update `session-handoff.md`.
10. Stop if a dependency or infrastructure blocker prevents truthful verification.

## Forbidden shortcuts
- Do not mark tests as passing without running them.
- Do not create fake Telegram message IDs.
- Do not implement payment providers in this phase.
- Do not implement product handlers in this phase.
- Do not add speculative abstractions without a current dependency.
- Do not silently rewrite architecture decisions.

## Exit condition
Phase 1 is complete only when `FND-001` through `FND-004` are `passing`, repository verification is reproducible, and the handoff clearly points to Phase 2.

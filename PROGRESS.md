# PROGRESS

## Current Verified State
- Phase: 6 — Hardening & Production — implementation in progress.
- Phase 5 — Delivery & Commerce is verified and passing.
- Phase 5 CI evidence: GitHub Actions run `34711911244` completed successfully on commit `abde684c01174535fe7b0fd17d52a10d6a211b7a`.
- Phase 5 verification: 56 tests passed, Alembic upgraded through `0005_delivery`, Ruff check/format passed, mypy passed, compileall passed, and the full purchase → payment verification → multi-file delivery E2E passed.
- Phase 6 standard verification gate remains `pytest`, `ruff check .`, `ruff format --check .`, `mypy src`, `python -m compileall -q src`, plus Alembic/PostgreSQL/Redis integration and deployment smoke testing when applicable.
- Phase 6 must not be marked passing merely because code exists; every Definition of Done item needs executable evidence.
- Phase 6 branch: `phase-6-hardening-production`.

## Phase status
| Phase | Status | Exit condition |
|---|---|---|
| 1 Foundation & Harness | passing | FND-001..FND-004 passing with reproducible evidence |
| 2 Product & Telegram Intake | passing | admin can intake, classify, collect metadata, confirm, publish boundary |
| 3 Store & Admin | passing | store browsing/admin management works and full verification passes |
| 4 Orders & Payment | passing | order lifecycle, price snapshots, idempotent payments, Zarinpal verification, callback security, and full checks pass |
| 5 Delivery & Commerce | passing | paid multi-file delivery is reliable, secure, retryable, auditable, and E2E verified |
| 6 Hardening & Scale | in_progress | security, observability, recovery, webhooks, production readiness |

## Phase 6 active scope
### Security
- Admin authorization and callback/webhook validation audit.
- Secret handling and environment isolation audit.
- Telegram input validation and file access control.
- Rate limiting and replay/idempotency review.
- Sensitive logging review: no tokens, credentials, payment secrets, or raw provider payloads in logs.

### Reliability
- External-service timeout, retry, exponential backoff, circuit/failure handling, and idempotency review.
- Verify duplicate-safe Order, Payment, Publication, and Delivery operations.

### Redis
- Distributed locks, FSM state, idempotency, TTL, invalidation, and Redis-failure behavior.

### Database
- Indexes, foreign keys, constraints, transaction boundaries, migration safety, connection pooling, and important query review.

### Observability
- Structured logs with correlation IDs and traceable commerce events.
- Metrics for orders, payments, payment failures, delivery, delivery failures, and Telegram API errors where useful.

### Health
- Application, PostgreSQL, and Redis health checks without business side effects.

### Testing
- Unit/integration/E2E plus payment timeout, Telegram failure, Redis restart, DB failure, duplicate callbacks/delivery, partial delivery, invalid admin callback, malicious customer callback, and concurrency scenarios.

### Backup/recovery
- PostgreSQL backup, restore, migration recovery, and incident-recovery documentation/testing.
- Telegram storage references must not be the only source of recoverable business metadata.

### Production deployment
- Docker/runtime configuration, environment variables, database, Redis, bot, migrations, deployment, rollback, backup, restore, monitoring, logs, and incident recovery.

### Future web/WooCommerce architecture
- Keep Commerce Core provider/adapter agnostic so Telegram, Web, WooCommerce, and external webhooks can reuse business logic without duplicating it.
- Do not prematurely implement a concrete WooCommerce integration.

### Fresh-agent test
A new agent with repository access only must be able to identify project purpose, architecture, execution/testing procedure, verified state, remaining features, decisions, blockers, and next action.

## Phase 6 gate
Phase 6 remains `in_progress`. Do not claim production-ready until all security, reliability, Redis, database, observability, health, failure/concurrency, backup/restore, deployment, future-integration architecture, and fresh-agent requirements are independently verified with evidence.

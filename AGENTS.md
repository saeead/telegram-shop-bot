# AGENTS.md — Telegram File Store

## Mission
Build a scalable Telegram-first digital marketplace for selling STL/3D-print-ready files. The repository is the system of record for architecture, progress, feature state, verification evidence, and decisions.

## First read
1. `README.md`
2. `PROGRESS.md`
3. `feature_list.json`
4. `DECISIONS.md`
5. relevant module `ARCHITECTURE.md` / `CONSTRAINTS.md`
6. `session-handoff.md` when present

## Operating rules
- Work on exactly one feature at a time. Only one feature may be `in_progress`.
- Do not implement a later phase to compensate for an unfinished earlier phase unless explicitly required by a documented dependency.
- Before changing code, identify the feature ID, acceptance criteria, affected modules, and verification path.
- Prefer small, reversible changes with tests.
- Do not claim a feature is complete without executable verification and recorded evidence.
- Keep domain logic independent of Telegram handlers and payment-provider SDKs.
- Never store customer product files on the application server as part of normal operation. Telegram is the file storage layer; the database stores Telegram references and metadata.
- Never put secrets in source control. Use environment variables and `.env.example`.
- Payment callbacks/webhooks must be idempotent.
- Product publication and delivery must be retry-safe and auditable.
- Preserve backward compatibility at service boundaries.
- Update documentation and state files together with meaningful code changes.

## Standard commands
- Setup: `./init.sh`
- Tests: `pytest`
- Fast checks: `./scripts/check.sh`
- Lint/format: `ruff check . && ruff format --check .`
- Type check: `mypy src`
- Start: `python -m app.main`

## Definition of done
A feature is done only when:
1. implementation is complete;
2. relevant unit/integration/e2e tests pass;
3. lint/type checks pass where applicable;
4. failure paths are considered;
5. user-visible behavior is verified;
6. evidence is recorded in `feature_list.json` and `PROGRESS.md`;
7. docs/constraints are updated if behavior or architecture changed;
8. no unrelated feature was silently modified;
9. the repository is left in a clean, runnable state.

## Architecture boundary
`domain` must not import Telegram, Redis, SQLAlchemy, or payment SDKs. `application` orchestrates use cases through ports/interfaces. `infrastructure` implements those ports. `presentation` and `telegram` translate external input into application commands.

## Fresh-session test
A new agent with repository access only must be able to answer: what is this system, how is it organized, how is it run, how is it verified, and what should be done next. If not, improve the repository map before adding complexity.

## End-of-session protocol
Run verification, update `PROGRESS.md`, `feature_list.json`, and `session-handoff.md`, record blockers/risks, and leave a clear next action. Do not leave hidden TODOs or half-finished migrations.

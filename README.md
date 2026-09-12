# Telegram File Store

Scalable Telegram-first digital commerce backend for selling STL and 3D-print-ready files. Product file bytes remain in Telegram channels; PostgreSQL stores product metadata, Telegram references, orders, payments, delivery state, and audit history.

## Current status

- Phases 1–5: **verified and passing** with executable CI evidence.
- Phase 6 — Hardening & Production: **in progress**.
- Production-ready: **NOT VERIFIED** until every Phase 6 Definition of Done item has evidence.

The durable source of truth is the repository, not chat history. Start with `AGENTS.md`, `PROGRESS.md`, `feature_list.json`, `DECISIONS.md`, `CHANGELOG.md`, `session-handoff.md`, and `quality-document.md`.

## Product channels

- **Store channel (public):** preview media only, grouped by product, with purchase CTA.
- **Archive channel (private):** previews + original/main files; delivery source.
- **Backup channel (private):** previews + original/main files; delivery fallback/source.

## Core flow

```text
Admin intake
   ↓
Product + files
   ↓
Store publication
   ↓
Buy
   ↓
Order
   ↓
Payment provider
   ↓
Provider verification
   ↓
PAID order
   ↓
DeliveryService
   ↓
All purchased main files
```

Delivery is independently orchestrated and tracked per `(order_id, file_id)`.

## Architecture

```text
                    Commerce Core
                         ↑
             ┌───────────┼───────────┐
          Telegram      Web       WooCommerce
          adapters    future       future

Domain
  ↓
Application ports/services
  ↓
Infrastructure adapters
  ↓
PostgreSQL / Redis / Telegram / Payment provider
```

Business logic must remain independent of aiogram, SQLAlchemy, Redis implementation details, payment SDKs, and future WooCommerce adapters.

## Stack

- Python 3.12+
- aiogram 3.x
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Redis
- pytest / pytest-asyncio
- Ruff
- mypy
- Docker service containers for CI

## Development

```bash
cp .env.example .env
./init.sh
pytest
ruff check .
ruff format --check .
mypy src
python -m compileall -q src
bash ./scripts/check.sh
```

Run PostgreSQL and Redis for the full integration suite.

## Production documentation

- `docs/production/backup-recovery.md` — PostgreSQL backup/restore and migration recovery procedure.
- `docs/production/deployment.md` — deployment, rollback, monitoring, and incident recovery.
- `quality-document.md` — evidence-based production-readiness audit.

## Phase history

| Phase | Status |
|---|---|
| 1 Foundation & Harness | passing |
| 2 Product & Telegram Intake | passing |
| 3 Store & Admin | passing |
| 4 Orders & Payment | passing |
| 5 Delivery & Commerce | passing |
| 6 Hardening & Production | in progress |

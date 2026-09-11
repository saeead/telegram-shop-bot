# Telegram File Store

Scalable Telegram-first digital commerce backend for selling STL and 3D-print-ready files. The product files themselves are kept in Telegram channels; the application database stores product metadata, Telegram message/file references, orders, payments, delivery state, and audit history.

## Product channels
- **Store channel (public):** preview media only, grouped by product, with purchase CTA.
- **Archive channel (private):** previews + original/main files; operational source for delivery.
- **Backup channel (private):** previews + original/main files; secondary delivery/source channel.

## Core flow
1. Admin forwards a batch of media/files to the bot.
2. Intake classifies images/previews vs main archives (`stl`, `zip`, `rar`, `7z` and future configured types).
3. Bot creates a product code and asks the admin for product name, category, price, and future metadata.
4. Admin reviews and confirms.
5. Bot publishes the preview group to Store and the complete set to Archive and Backup.
6. Customer opens purchase flow from Store.
7. Order is created and payment is initiated through a provider abstraction (initially Zarinpal for IRR; crypto provider to be selected later).
8. Verified payment changes the order to paid exactly once.
9. Delivery retrieves Telegram references and sends all main files to the customer, with retry-safe delivery tracking.

## Architecture
The system is intentionally split into domain, application, infrastructure, and presentation/adapter layers. Telegram and payment providers are adapters, not the business core.

## Harness
The project follows the Learn Harness Engineering principles: repository-as-spec, a small `AGENTS.md` landing page, machine-readable feature state, durable progress, session handoff, verification evidence, and clean-state checks. Critical knowledge must live in the repository because a fresh agent cannot rely on chat history. See the referenced source: urlLearn Harness Engineering — Repository as System of Recordhttps://walkinglabs.github.io/learn-harness-engineering/en/lectures/lecture-03-why-the-repository-must-become-the-system-of-record/

## Stack baseline
- Python 3.12+
- aiogram 3.x
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Redis
- pytest
- Ruff
- mypy
- Docker Compose for local dependencies

Exact dependency versions are pinned during Phase 1 after checking current compatibility.

## Development
```bash
cp .env.example .env
./init.sh
pytest
python -m app.main
```

The initial scaffold intentionally contains no production secrets and no payment integration. Phase 1 establishes the runnable foundation before feature implementation.

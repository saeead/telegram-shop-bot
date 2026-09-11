# Architecture Decisions

## ADR-001 — Repository is the system of record
**Status:** accepted

Critical architecture, progress, verification evidence, constraints, and handoff state must be committed to the repository. Chat history is not a durable project dependency.

## ADR-002 — Commerce core is provider-agnostic
**Status:** accepted

Business logic must not depend directly on aiogram, Zarinpal SDKs, crypto SDKs, or WooCommerce. External systems implement ports/interfaces in infrastructure/adapters.

## ADR-003 — Telegram is the product-file storage layer
**Status:** accepted

Normal product file bytes are not persisted by the application server. Telegram channel message/file references are persisted in PostgreSQL. Archive and Backup provide operational redundancy.

## ADR-004 — Product is the aggregate, files are children
**Status:** accepted

A product may contain one or many previews and one or many main files. File classification is represented explicitly instead of assuming a one-preview/one-main-file relationship.

## ADR-005 — Payment is idempotent
**Status:** accepted

Repeated provider callbacks must not create duplicate successful payments, orders, or deliveries.

## ADR-006 — Initialization precedes feature implementation
**Status:** accepted

Phase 1 establishes a runnable baseline and verification harness before feature implementation. This reduces false progress and makes later agent sessions reproducible.

## ADR-007 — Async persistence foundation
**Status:** accepted

The application uses SQLAlchemy's asyncio extension with `asyncpg` for PostgreSQL. Alembic runs migrations through SQLAlchemy's async engine bridge. SQLAlchemy's asyncio extra is declared explicitly so the required async runtime support is installed with the application dependencies.

## ADR-008 — Public Store publishes previews, never main files
**Status:** accepted

The public Store channel may publish preview media and product presentation data, but main downloadable product files remain private and are referenced only through the commerce/delivery workflow.

## ADR-009 — Presentation formatting stays outside the domain
**Status:** accepted

Telegram captions, inline keyboards, media-group composition, callback payloads, and navigation presentation are adapter/application concerns. The Product domain remains independent of Telegram and presentation formatting.

## ADR-010 — Publication is idempotent
**Status:** accepted

Store publication and republish operations must be safe to retry. A stable publication identity is used to prevent duplicate public Store messages while allowing state reconciliation.

## ADR-011 — Admin authorization is server-side
**Status:** accepted

Every admin command and callback is authorized from trusted server-side actor identity. Callback data is treated as untrusted input and cannot grant administrative privileges.

## ADR-012 — Historical products are retained
**Status:** accepted

Hide/archive operations change visibility/status and audit state without deleting historical product records. This preserves commerce and operational history for later phases.

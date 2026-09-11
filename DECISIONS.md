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

Phase 1 establishes a runnable baseline and verification harness before business features. This reduces false progress and makes later agent sessions reproducible.

# Architecture Decisions

## ADR-001 — Repository is the system of record
**Status:** accepted

Critical architecture, progress, verification evidence, constraints, and handoff state must be committed to the repository. Chat history is not a durable project dependency.

## ADR-002 — Commerce core is provider-agnostic
**Status:** accepted

Business logic must not depend directly on aiogram, Zarinpal SDKs, crypto SDKs, or WooCommerce. External systems implement ports/interfaces in infrastructure/adapters.

## ADR-003 — Telegram is the product-file storage layer
**Status:** accepted

Normal product file bytes are not persisted by the application server. Telegram channel message/file references are persisted in PostgreSQL.

## ADR-004 — Product is the aggregate, files are children
**Status:** accepted

A product may contain one or many previews and one or many main files. File classification is represented explicitly.

## ADR-005 — Payment is idempotent
**Status:** accepted

Repeated provider callbacks must not create duplicate successful payments, orders, or deliveries. Unique idempotency/provider-reference constraints and application-level replay checks enforce this boundary.

## ADR-006 — Initialization precedes feature implementation
**Status:** accepted

Phase 1 establishes a runnable baseline and verification harness before feature implementation.

## ADR-007 — Async persistence foundation
**Status:** accepted

The application uses SQLAlchemy asyncio with asyncpg for PostgreSQL and Alembic for migrations.

## ADR-008 — Public Store publishes previews, never main files
**Status:** accepted

The public Store channel may publish preview media and product presentation data, but main downloadable files remain private.

## ADR-009 — Presentation formatting stays outside the domain
**Status:** accepted

Telegram captions, keyboards, media groups, callback payloads, and navigation are adapter/application concerns.

## ADR-010 — Publication is idempotent
**Status:** accepted

Store publication and republish operations must be safe to retry without duplicate public Store messages.

## ADR-011 — Admin authorization is server-side
**Status:** accepted

Every admin command and callback is authorized from trusted server-side actor identity.

## ADR-012 — Historical products are retained
**Status:** accepted

Hide/archive operations change visibility/status and audit state without deleting historical product records.

## ADR-013 — Orders snapshot commercial terms
**Status:** accepted

Order items store the product name, unit price, currency, and quantity used at purchase time. Later Product edits cannot mutate an existing order's price.

## ADR-014 — Payment providers are ports
**Status:** accepted

Order/payment application logic depends only on `PaymentProvider`. Zarinpal and future crypto providers are adapters. No provider-specific SDK types or semantics are allowed in the Order domain.

## ADR-015 — Provider verification is the source of payment truth
**Status:** accepted

A browser callback is untrusted input. `Status=OK` only permits verification; an order becomes paid only after the provider adapter validates the verification response and the amount/provider/order/authority checks succeed.

## ADR-016 — Payment attempts are immutable ledger records
**Status:** accepted

Each provider attempt records provider, reference, amount, status, timestamps, idempotency key, and safe metadata. Credentials, merchant secrets, card data, and other payment secrets are never persisted.

## ADR-017 — Delivery is downstream of payment
**Status:** accepted

Phase 4 marks an order paid but does not call or implement delivery. Fulfillment is a separate Phase 5 concern and must consume the paid state idempotently.

## ADR-018 — Crypto provider selection is deferred
**Status:** accepted

Phase 4 defines only a crypto-provider abstraction. A concrete gateway is intentionally deferred until a separate architecture decision selects the provider and settlement model.

## ADR-019 — Delivery is tracked per purchased file
**Status:** accepted

A delivery record is uniquely identified by `(order_id, file_id)`. Successful files are never resent during normal retry, while failed/partial files remain independently retryable. This prevents one failed file from invalidating already delivered files.

## ADR-020 — Customer authorization is based on paid order ownership
**Status:** accepted

Delivery requests must resolve the order, verify the requesting Telegram user owns it, require `PAID`, and verify any requested product code belongs to that order. Product codes alone are never authorization credentials.

## ADR-021 — Delivery source failures are adapter concerns
**Status:** accepted

Archive/Backup Telegram failures are translated into a safe `DeliverySourceError`. The Delivery domain stores only safe failure text and never stores raw Telegram exceptions, tokens, or credentials.

# Architecture

## Layers
- `domain`: pure business entities, value objects, domain rules.
- `application`: use cases, orchestration, ports/interfaces.
- `infrastructure`: PostgreSQL, Redis, Telegram API adapter, payment providers, external integrations.
- `presentation`: transport-specific handlers, DTOs, keyboards, FSM flows.

## Dependency direction
`presentation -> application -> domain`
`infrastructure -> application/domain`
`domain -> nothing external`

## Core aggregates
- Product
- Order
- Payment
- Customer
- Admin

## Product publication
A publication use case writes Telegram references and product publication state atomically from the application's perspective, with compensating/retry logic for external Telegram operations.

## Future website integration
Expose application use cases through an HTTP/webhook adapter later. Do not put WooCommerce logic into Telegram handlers.

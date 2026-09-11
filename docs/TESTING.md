# Testing Strategy

## Unit
Pure domain rules, classification, pricing, state transitions, idempotency decisions.

## Integration
PostgreSQL repositories, Redis state, Telegram adapter with fake/contract transport, payment provider adapters.

## E2E
Admin intake → confirmation → publication → customer purchase → payment → delivery.

## Failure tests
- duplicate payment callback
- Telegram send failure and retry
- partial publication
- Redis restart
- PostgreSQL restart
- invalid admin input
- customer attempts to access unpaid product
- multi-file delivery failure

Every passing feature must have reproducible verification evidence.

# Observability

Use structured logs with correlation IDs and event names.

Important events include:
- intake_started
- product_draft_created
- product_confirmed
- product_published
- payment_created
- payment_callback_received
- payment_verified
- delivery_started
- delivery_file_sent
- delivery_failed
- admin_action

Metrics/health checks will be added in Phase 6. Never emit secrets or sensitive payment data.

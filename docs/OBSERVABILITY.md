# Observability

Use structured logs with correlation IDs and named business events.

## Primitives

- `new_correlation_id` / `get_correlation_id`
- `log_event(logger, event, **fields)` (sensitive field names filtered)
- `increment_metric` / `snapshot_metrics` / `clear_metrics`
- `StructuredJsonFormatter` for machine-readable logs

## Events

- intake_started
- product_draft_created
- product_confirmed
- product_published
- order_created
- payment_created
- payment_callback_received
- payment_verified
- delivery_started
- delivery_finished
- delivery_file_sent
- delivery_failed
- admin_action

## Metrics (service boundaries)

- `orders_total` — incremented on successful order creation
- `payments_total` — incremented on successful payment verification
- `payment_failures_total` — provider timeout/error or failed verification
- `delivery_total` — order fully delivered
- `delivery_failures_total` — delivery finished with failed files

Never emit secrets, tokens, merchant IDs, or raw provider payloads.

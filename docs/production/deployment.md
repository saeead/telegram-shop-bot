# Production Deployment

## Required configuration

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_IDS`
- `TELEGRAM_STORE_CHANNEL_ID`
- `TELEGRAM_ARCHIVE_CHANNEL_ID`
- `TELEGRAM_BACKUP_CHANNEL_ID`
- `DATABASE_URL`
- `REDIS_URL`
- `ZARINPAL_MERCHANT_ID`
- `ZARINPAL_SANDBOX`
- `PAYMENT_CALLBACK_URL`

Secrets must be injected by the runtime secret manager and never committed to `.env`, logs, CI output, or documentation.

## Deployment sequence

1. Build the pinned application image.
2. Provision/verify PostgreSQL and Redis.
3. Take a PostgreSQL backup.
4. Deploy the new application version in a controlled rollout.
5. Run `alembic upgrade head`.
6. Run application/PostgreSQL/Redis health checks.
7. Start Telegram workers.
8. Monitor structured logs, metrics, payment callbacks, publication, and delivery errors.

## Rollback

1. Stop the affected application workers.
2. Preserve logs and incident metadata.
3. If schema is backward-compatible, redeploy the previous application image.
4. If the migration itself is incompatible, restore the database backup according to `backup-recovery.md` rather than blindly downgrading production data.
5. Re-run health checks and the verification harness.
6. Reconcile payment and delivery state before reopening commerce operations.

## Monitoring

At minimum monitor:

- application health;
- PostgreSQL health and connection saturation;
- Redis availability;
- `orders_total`;
- `payments_total`;
- `payment_failures_total`;
- `delivery_total`;
- `delivery_failures_total`;
- Telegram API errors;
- callback/payment replay anomalies;
- delivery partial/failed states.

## Incident recovery

- Correlate events using correlation IDs.
- Never copy secrets or provider credentials into incident tickets.
- Preserve business-state evidence before manual intervention.
- Prefer idempotent retries over manual duplicate operations.

**Current status: NOT VERIFIED.** Deployment and rollback smoke tests still need executable production-like evidence.

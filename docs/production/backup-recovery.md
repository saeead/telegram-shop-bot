# PostgreSQL Backup & Recovery

## Scope
PostgreSQL is the source of truth for product metadata, orders, payments, delivery tracking, audit records, and Telegram references.

Telegram Archive/Backup channels are file-storage sources, not the sole source of business metadata.

## Backup strategy

1. Run scheduled PostgreSQL logical backups with `pg_dump --format=custom`.
2. Encrypt backups at rest using the deployment platform's secret/key-management facility.
3. Keep multiple generations according to the operator retention policy.
4. Store at least one backup copy outside the primary runtime host.
5. Never put database passwords or backup encryption keys in the repository.
6. Record backup success/failure as an operational metric/alert.

Example (operator shell):

```bash
pg_dump --format=custom --file=telegram-file-store.dump "$DATABASE_URL"
```

## Restore procedure

1. Stop application workers that can mutate business state.
2. Provision a clean PostgreSQL database.
3. Restore the dump:

```bash
pg_restore --clean --if-exists --dbname="$DATABASE_URL" telegram-file-store.dump
```

4. Run `alembic current` and confirm the expected migration revision.
5. Run the complete test suite and repository verification harness.
6. Start workers only after health checks pass.
7. Reconcile Telegram file references and delivery records before reopening customer delivery.

## Migration recovery

- Never edit an already-applied migration in place.
- Add a corrective migration for schema changes.
- Before production migration, take a fresh backup.
- If a migration fails transactionally, inspect the failed revision and database state before retrying.
- If rollback is unsafe, restore to a clean database and apply the known-good migration chain.

## Restore drill

A production-ready release requires a scheduled restore drill that proves:

- backup can be read;
- schema and data restore successfully;
- order/payment/delivery business state remains coherent;
- Telegram references remain recoverable;
- application and health checks pass after restore.

**Current status: NOT VERIFIED.** The procedure is documented; an actual backup/restore drill still needs executable evidence.

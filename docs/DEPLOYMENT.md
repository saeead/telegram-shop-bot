# Deployment

Phase 1 uses Docker Compose for local PostgreSQL/Redis. Production deployment is intentionally deferred until the application boundaries and recovery behavior are verified.

Production must provide:
- secret management
- persistent PostgreSQL
- Redis availability appropriate to workload
- TLS for webhooks
- health checks
- structured logs
- database migrations
- backup/restore procedure
- controlled rollout/rollback

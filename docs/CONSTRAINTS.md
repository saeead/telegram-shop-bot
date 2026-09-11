# Global Constraints

- MUST keep business logic out of Telegram handlers.
- MUST NOT store product file bytes on the app server during normal operation.
- MUST store enough Telegram references to reproduce delivery.
- MUST treat provider callbacks as untrusted, validate them, and make processing idempotent.
- MUST use UTC internally for persisted timestamps.
- MUST NOT log bot tokens, merchant secrets, API keys, or full payment credentials.
- MUST audit privileged product/price/publication actions.
- MUST support multi-preview and multi-main-file products.
- MUST distinguish preview files from paid main files.
- MUST require admin confirmation before publication.
- MUST make retryable external operations safe.

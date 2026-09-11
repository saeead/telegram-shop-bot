# Security

- Secrets only through environment/secret manager.
- Admin authorization must be explicit and allow-list based.
- Validate all callback data and external webhook signatures/credentials.
- Rate-limit sensitive endpoints/actions.
- Do not trust Telegram user-provided metadata for authorization.
- Do not expose private Archive/Backup channel identifiers in public UI unless necessary.
- Log correlation IDs, not secrets.
- Payment replay and duplicate delivery are security/reliability concerns, not edge cases.

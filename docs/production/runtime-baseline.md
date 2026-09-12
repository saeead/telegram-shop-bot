# Production Runtime Baseline

Phase 6 hardening establishes a safer container baseline, but this document does **not** claim production readiness.

## Container

- Python 3.12 slim base image.
- Bytecode generation disabled and stdout/stderr unbuffered.
- Application runs as an unprivileged `appuser` (UID 10001).
- Dependencies are installed without retaining pip's download cache.

## Compose

The production-oriented compose definition includes the application, PostgreSQL, and Redis services.

- Application depends on healthy PostgreSQL and Redis services.
- PostgreSQL and Redis are bound to loopback on the host by default.
- Required Telegram configuration is supplied through environment variables rather than committed secrets.
- Application restart policy is `unless-stopped`.
- PostgreSQL and Redis have container health checks.

## Verification

CI must execute both the standard repository verification harness and a Docker image build. A successful image build proves the container definition is buildable; it does not prove deployment, rollback, backup/restore, Telegram connectivity, payment connectivity, or production readiness.

## Remaining Phase 6 work

- Runtime health endpoint/integration wiring where required by the final deployment model.
- Real deployment smoke test.
- Rollback test.
- Backup/restore drill.
- Failure-injection and concurrency verification.
- Final security and repository audit.

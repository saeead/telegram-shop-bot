# PROGRESS

## Current Verified State
- Phase: 6 — Hardening & Production — implementation in progress (`OPS-001`).
- Phase 5 verified; product runtime on main (PR #10); security baseline on main (PR #9); failure-injection suite on main (PR #11, CI `34717314211`).
- Branch `phase-6-ops-remaining` adds executable coverage for remaining OPS gaps:
  - Backup drill: `scripts/backup_restore_drill.sh` + `tests/integration/test_backup_restore_drill.py`
  - Deploy smoke: `scripts/deploy_smoke.sh`
  - Infra failure modes: `tests/integration/test_infra_failure_modes.py` (unreachable DB/Redis health, lock after key loss)
  - Observability wiring: order/payment/delivery metrics at service boundaries + unit coverage
  - Fresh-agent: `scripts/fresh_agent_check.py` + `docs/production/fresh-agent.md` (also run from `scripts/check.sh`)
- Production Ready is **not** claimed until CI is green on this branch and evidence is recorded on main.

## Phase status
| Phase | Status | Exit condition |
|---|---|---|
| 1 Foundation & Harness | passing | FND-001..FND-004 passing with reproducible evidence |
| 2 Product & Telegram Intake | passing | admin can intake, classify, collect metadata, confirm, publish boundary |
| 3 Store & Admin | passing | store browsing/admin management works and full verification passes |
| 4 Orders & Payment | passing | order lifecycle, price snapshots, idempotent payments, Zarinpal verification, callback security, and full checks pass |
| 5 Delivery & Commerce | passing | paid multi-file delivery is reliable, secure, retryable, auditable, and E2E verified |
| 6 Hardening & Scale | in_progress | security, observability, recovery, webhooks, production readiness |

## Phase 6 gate
Do not claim production-ready until all security, reliability, Redis, database, observability, health, failure/concurrency, backup/restore, deployment, and fresh-agent requirements are independently verified with evidence.

#!/usr/bin/env bash
# Production-like deploy smoke: migrations, import surface, health helpers, image build.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "deploy_smoke_started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

PYTHONPATH=src python - <<'PY'
from app.application.health import HealthStatus
from app.bootstrap import build_runtime
from app.config.settings import Settings
from app.infrastructure.observability import snapshot_metrics

# Import surface must remain loadable without side effects.
assert HealthStatus(True, True, True).healthy is True
assert isinstance(snapshot_metrics(), dict)
Settings  # settings class importable
build_runtime  # composition root importable
print("import_surface_ok=1")
PY

if [[ -n "${DATABASE_URL:-}" ]]; then
  alembic current
  echo "alembic_current_ok=1"
else
  echo "alembic_current_skipped=1"
fi

if [[ "${DEPLOY_SMOKE_DOCKER:-0}" == "1" ]]; then
  docker build -f docker/Dockerfile .
  echo "docker_build_ok=1"
else
  echo "docker_build_skipped=1"
fi

echo "deploy_smoke_finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Deploy smoke completed."

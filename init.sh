#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "Repository: $(pwd)"
INSTALL_CMD="python -m pip install -e '.[dev]'"
VERIFY_CMD="python -m pytest"
START_CMD="python -m app.main"
echo "Installing dependencies..."
eval "$INSTALL_CMD"
echo "Running baseline verification..."
eval "$VERIFY_CMD"
echo "Baseline verification passed."
echo "Start command: $START_CMD"
if [[ "${RUN_START_COMMAND:-0}" == "1" ]]; then
  exec bash -lc "$START_CMD"
fi

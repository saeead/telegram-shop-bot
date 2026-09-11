#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest
ruff check .
ruff format --check .
python -m mypy src
python - <<'PY'
import json
from pathlib import Path
p = Path('feature_list.json')
data = json.loads(p.read_text())
active = [f for f in data['features'] if f['status'] == 'in_progress']
assert len(active) <= 1, 'More than one feature is in_progress'
for f in data['features']:
    if f['status'] == 'passing':
        assert f['evidence'].strip(), f"Passing feature lacks evidence: {f['id']}"
print('Harness state validation passed.')
PY

"""Fresh-agent readiness check: required docs answer the onboarding questions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "PROGRESS.md",
    "feature_list.json",
    "AGENTS.md",
    "session-handoff.md",
    "docs/ARCHITECTURE.md",
    "docs/CONSTRAINTS.md",
    "scripts/check.sh",
)

REQUIRED_PHRASES = {
    "README.md": ("Telegram", "pytest", "check.sh"),
    "PROGRESS.md": ("Phase", "in_progress"),
    "AGENTS.md": ("one feature", "feature_list.json"),
    "session-handoff.md": ("Next action", "OPS-001"),
}


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing:{rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            errors.append(f"empty:{rel}")
        for phrase in REQUIRED_PHRASES.get(rel, ()):
            if phrase.lower() not in text.lower():
                errors.append(f"missing_phrase:{rel}:{phrase}")

    features = json.loads((ROOT / "feature_list.json").read_text(encoding="utf-8"))
    active = [f for f in features["features"] if f["status"] == "in_progress"]
    if len(active) > 1:
        errors.append("harness:more_than_one_in_progress")
    for feature in features["features"]:
        if feature["status"] == "passing" and not str(feature.get("evidence", "")).strip():
            errors.append(f"harness:passing_without_evidence:{feature['id']}")

    if errors:
        print("fresh_agent_check_failed")
        for item in errors:
            print(item)
        return 1
    print("fresh_agent_check_ok=1")
    print(f"in_progress={[f['id'] for f in active]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

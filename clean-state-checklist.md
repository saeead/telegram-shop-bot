# Clean-State Checklist

Before ending every agent session:

- [ ] `pytest` passes.
- [ ] `ruff check .` passes.
- [ ] `ruff format --check .` passes.
- [ ] `mypy src` passes when applicable.
- [ ] Only one feature is `in_progress` (or zero between tasks).
- [ ] No feature is marked `passing` without evidence.
- [ ] `PROGRESS.md` reflects reality.
- [ ] `session-handoff.md` has the next best action.
- [ ] Architecture/constraints docs changed with architecture changes.
- [ ] No secrets, customer file bytes, or local runtime artifacts were committed.
- [ ] No hidden or unrecorded half-finished work remains.

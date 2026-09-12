# Fresh-agent readiness

A new agent with repository access only must be able to answer:

1. What is this system? → `README.md`
2. How is it organized? → `docs/ARCHITECTURE.md`, `AGENTS.md`
3. How is it run and verified? → `scripts/check.sh`, `docs/TESTING.md`
4. What is verified state? → `PROGRESS.md`, `feature_list.json`
5. What is next? → `session-handoff.md`

## Executable check

```bash
python scripts/fresh_agent_check.py
```

Exit code 0 means required documents exist and harness invariants hold.

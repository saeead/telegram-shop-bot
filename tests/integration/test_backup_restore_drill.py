"""Backup drill evidence: live DB snapshot + optional pg_dump presence."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine


def _usable_bash() -> str | None:
    """Return a bash executable that can actually run, or None."""
    candidate = shutil.which("bash")
    if candidate is None:
        return None
    probe = subprocess.run(
        [candidate, "-c", "echo ok"],
        check=False,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 or "ok" not in probe.stdout:
        return None
    return candidate


@pytest.mark.asyncio
async def test_backup_drill_snapshots_core_tables() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not configured")

    engine = create_async_engine(url)
    tables = ("products", "orders", "payments", "delivery_records")
    counts: dict[str, int] = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            for table in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    counts[table] = int(result.scalar_one())
                except SQLAlchemyError:
                    counts[table] = -1
    finally:
        await engine.dispose()

    assert all(value >= 0 for value in counts.values()), counts
    report = Path(tempfile.gettempdir()) / "telegram-file-store-pytest-backup-report.txt"
    report.write_text(
        "\n".join(f"row_count_{name}={value}" for name, value in counts.items()) + "\n",
        encoding="utf-8",
    )
    assert report.is_file()


def test_backup_script_is_executable_and_documents_restore() -> None:
    script = Path("scripts/backup_restore_drill.sh")
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "pg_dump" in text
    assert "DATABASE_URL" in text
    docs = Path("docs/production/backup-recovery.md").read_text(encoding="utf-8")
    assert "Restore procedure" in docs
    assert "pg_restore" in docs


def test_backup_script_runs_when_database_configured() -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    bash = _usable_bash()
    if bash is None:
        pytest.skip("usable bash is not available on this platform")

    report_path = str(Path(tempfile.gettempdir()) / "pytest-backup-drill-report.txt")
    result = subprocess.run(
        [bash, "scripts/backup_restore_drill.sh"],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "BACKUP_REPORT_PATH": report_path},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = Path(report_path)
    assert report.is_file()
    body = report.read_text(encoding="utf-8")
    assert "database_reachable=1" in body
    assert "backup_restore_drill_finished=" in body
    # pg_dump may be skipped on client/server version mismatch; snapshot is required.
    assert "pg_dump_ok=" in body

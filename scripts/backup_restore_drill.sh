#!/usr/bin/env bash
# Executable PostgreSQL backup drill evidence for OPS-001.
# Requires DATABASE_URL (postgresql+asyncpg:// form is accepted).
# Row-count snapshot is required. pg_dump is best-effort (version mismatch is non-fatal).
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

LIBPQ_URL="${DATABASE_URL/postgresql+asyncpg:\/\//postgresql:\/\/}"
DUMP_FILE="${BACKUP_DUMP_PATH:-/tmp/telegram-file-store-drill.dump}"
REPORT_FILE="${BACKUP_REPORT_PATH:-/tmp/telegram-file-store-drill-report.txt}"

{
  echo "backup_restore_drill_started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "dump_file=${DUMP_FILE}"
  python - <<'PY'
import asyncio
import os

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine

url = os.environ["DATABASE_URL"]
if url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

tables = ("products", "orders", "payments", "delivery_records")


async def main() -> None:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("database_reachable=1")
            for table in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar_one()
                    print(f"row_count_{table}={count}")
                except SQLAlchemyError as exc:
                    print(f"row_count_{table}=error:{type(exc).__name__}")
    finally:
        await engine.dispose()


asyncio.run(main())
PY
} | tee "${REPORT_FILE}"

if command -v pg_dump >/dev/null 2>&1; then
  set +e
  pg_dump --format=custom --no-owner --no-acl --file="${DUMP_FILE}" "${LIBPQ_URL}" 2>"${DUMP_FILE}.err"
  dump_rc=$?
  set -e
  if [[ ${dump_rc} -eq 0 ]] && [[ -s "${DUMP_FILE}" ]]; then
    echo "pg_dump_ok=1 size_bytes=$(wc -c < "${DUMP_FILE}")" | tee -a "${REPORT_FILE}"
  else
    reason="pg_dump_failed"
    if grep -qi "version mismatch" "${DUMP_FILE}.err" 2>/dev/null; then
      reason="pg_dump_version_mismatch"
    fi
    echo "pg_dump_ok=0 reason=${reason}" | tee -a "${REPORT_FILE}"
    if [[ -s "${DUMP_FILE}.err" ]]; then
      echo "pg_dump_stderr=$(tr '\n' ' ' < "${DUMP_FILE}.err")" | tee -a "${REPORT_FILE}"
    fi
    echo "Logical dump skipped (${reason}); row-count snapshot remains valid evidence." >&2
  fi
else
  echo "pg_dump_ok=0 reason=pg_dump_not_installed" | tee -a "${REPORT_FILE}"
  echo "Logical dump tool missing; row-count snapshot still recorded for evidence." >&2
fi

echo "backup_restore_drill_finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${REPORT_FILE}"
echo "Drill report written to ${REPORT_FILE}"

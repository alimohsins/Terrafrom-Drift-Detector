from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import ScanReport


class ScanStore:
    def __init__(self, path: Path):
        self.path = path
        self._init_db()

    def save(self, report: ScanReport) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                insert or replace into scans
                (scan_id, provider, started_at, completed_at, summary_json, report_json)
                values (?, ?, ?, ?, ?, ?)
                """,
                (
                    report.scan_id,
                    report.provider,
                    report.started_at.isoformat(),
                    report.completed_at.isoformat(),
                    json.dumps(report.to_dict()["summary"]),
                    report.to_json(),
                ),
            )

    def latest(self) -> dict | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute(
                "select report_json from scans order by completed_at desc limit 1"
            ).fetchone()
        return json.loads(row[0]) if row else None

    def list_scans(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """
                select scan_id, provider, started_at, completed_at, summary_json
                from scans
                order by completed_at desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "scan_id": row[0],
                "provider": row[1],
                "started_at": row[2],
                "completed_at": row[3],
                "summary": json.loads(row[4]),
            }
            for row in rows
        ]

    def _init_db(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                create table if not exists scans (
                    scan_id text primary key,
                    provider text not null,
                    started_at text not null,
                    completed_at text not null,
                    summary_json text not null,
                    report_json text not null
                )
                """
            )

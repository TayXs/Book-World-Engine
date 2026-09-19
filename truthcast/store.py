"""Job persistence. SQLite, because a queue that forgets is worse than none."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path

from .models import Job, JobState, utcnow

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    state       TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    payload     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_created_at ON jobs (created_at DESC);
"""


class JobStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    # --- sync core, so tests can drive it without an event loop ---------- #

    def save_sync(self, job: Job) -> Job:
        job.updated_at = utcnow()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO jobs (id, url, state, created_at, updated_at, payload)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       state=excluded.state,
                       updated_at=excluded.updated_at,
                       payload=excluded.payload""",
                (
                    job.id,
                    job.url,
                    job.state.value,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    job.model_dump_json(),
                ),
            )
        return job

    def get_sync(self, job_id: str) -> Job | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return Job.model_validate(json.loads(row["payload"])) if row else None

    def recent_sync(self, limit: int = 20) -> list[Job]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [Job.model_validate(json.loads(r["payload"])) for r in rows]

    def reset_running_sync(self) -> int:
        """On startup, jobs left mid-flight by a restart are failures, not ghosts."""
        stale = [
            job
            for job in self.recent_sync(limit=200)
            if job.state not in (JobState.DONE, JobState.FAILED)
        ]
        for job in stale:
            job.state = JobState.FAILED
            job.error = "Interrupted by a server restart. Run it again."
            self.save_sync(job)
        return len(stale)

    # --- async wrappers used by the API --------------------------------- #

    async def save(self, job: Job) -> Job:
        return await asyncio.to_thread(self.save_sync, job)

    async def get(self, job_id: str) -> Job | None:
        return await asyncio.to_thread(self.get_sync, job_id)

    async def recent(self, limit: int = 20) -> list[Job]:
        return await asyncio.to_thread(self.recent_sync, limit)

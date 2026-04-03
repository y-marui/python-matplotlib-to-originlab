"""SQLite job database for matplotlib-to-originlab-server."""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("MTO_DB_PATH", "jobs.db"))

_lock = threading.Lock()


def init_db() -> None:
    """Create the jobs table if it does not exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                status      TEXT NOT NULL DEFAULT 'queued',
                created_at  TEXT,
                started_at  TEXT,
                finished_at TEXT,
                figure_data TEXT,
                result_path TEXT,
                error       TEXT
            )
        """)


@contextmanager
def _connect():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_job(job_id: str, figure_data_json: str, created_at: str) -> None:
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO jobs (id, status, created_at, figure_data)"
            " VALUES (?, 'queued', ?, ?)",
            (job_id, created_at, figure_data_json),
        )


def get_job(job_id: str) -> dict | None:
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        return dict(row) if row else None


def update_job(job_id: str, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [job_id]
    with _lock, _connect() as conn:
        conn.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)


def get_next_queued_job() -> dict | None:
    """Return the oldest queued job, or None if the queue is empty."""
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE status = 'queued'"
            " ORDER BY created_at LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_all_jobs() -> list[dict]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def recover_running_jobs() -> None:
    """On server startup, re-queue any jobs that were interrupted mid-run."""
    with _lock, _connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'queued' WHERE status = 'running'"
        )

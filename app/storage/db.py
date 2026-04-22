"""SQLite connection helpers and schema initialization."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from ..config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    skill_id TEXT,
    status TEXT,
    input_json TEXT,
    output_json TEXT,
    error_text TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    run_id TEXT,
    tool_name TEXT,
    args_json TEXT,
    result_json TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_run_id ON tool_calls(run_id);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at);

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    version TEXT,
    enabled INTEGER,
    body_json TEXT,
    created_at TEXT,
    updated_at TEXT
);
"""


def _connect() -> sqlite3.Connection:
    settings = get_settings()
    path = settings.db_path_resolved
    conn = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(_SCHEMA)

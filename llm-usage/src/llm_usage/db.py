"""SQLite store for normalized usage records plus the aggregation queries.

Timestamps are stored as ISO8601 UTC strings ('YYYY-MM-DDTHH:MM:SSZ') so that
lexicographic comparison equals chronological comparison -- range filters are
plain string BETWEEN checks and the day bucket is ``substr(ts, 1, 10)``.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable

from llm_usage.models import UsageRecord

DEFAULT_DB_ENV = "LLM_USAGE_DB"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id        TEXT,
    ts                TEXT NOT NULL,
    model             TEXT NOT NULL,
    backend           TEXT NOT NULL,
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    latency_ms        REAL,
    cost_usd          REAL NOT NULL DEFAULT 0,
    status            TEXT NOT NULL DEFAULT 'success',
    source            TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_requests_reqid
    ON requests(request_id) WHERE request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_requests_ts ON requests(ts);
CREATE INDEX IF NOT EXISTS idx_requests_model ON requests(model);
"""

# Columns selected for the grouped aggregations, keyed by report dimension.
_GROUP_EXPR = {
    "model": "model",
    "backend": "backend",
    "day": "substr(ts, 1, 10)",
}

_TOP_METRIC = {
    "cost": "cost_usd_sum",
    "tokens": "total_tokens_sum",
    "requests": "requests",
}


def default_db_path() -> Path:
    """Where the store lives unless overridden by --db or $LLM_USAGE_DB."""
    env = os.environ.get(DEFAULT_DB_ENV)
    if env:
        return Path(env)
    return Path.home() / ".llm-usage" / "usage.db"


class UsageStore:
    """Thin wrapper around a SQLite connection holding the requests table."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "UsageStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- writes -------------------------------------------------------------

    def insert_many(self, records: Iterable[UsageRecord]) -> int:
        """Insert records, skipping duplicates by request_id. Returns count added."""
        inserted = 0
        with closing(self.conn.cursor()) as cur:
            for rec in records:
                if rec.request_id is not None and self._exists(cur, rec.request_id):
                    continue
                cur.execute(
                    """
                    INSERT INTO requests
                        (request_id, ts, model, backend, prompt_tokens,
                         completion_tokens, total_tokens, latency_ms, cost_usd,
                         status, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec.request_id,
                        rec.ts,
                        rec.model,
                        rec.backend,
                        rec.prompt_tokens,
                        rec.completion_tokens,
                        rec.total_tokens,
                        rec.latency_ms,
                        rec.cost_usd,
                        rec.status,
                        rec.source,
                    ),
                )
                inserted += 1
        self.conn.commit()
        return inserted

    @staticmethod
    def _exists(cur: sqlite3.Cursor, request_id: str) -> bool:
        cur.execute("SELECT 1 FROM requests WHERE request_id = ? LIMIT 1", (request_id,))
        return cur.fetchone() is not None

    # --- reads --------------------------------------------------------------

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]

    def aggregate(
        self,
        by: str = "model",
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        """Group requests by model/backend/day with token, latency and cost sums."""
        if by not in _GROUP_EXPR:
            raise ValueError(f"unknown group dimension: {by!r} (use model|backend|day)")
        group = _GROUP_EXPR[by]
        where, params = _time_clause(since, until)
        sql = f"""
            SELECT
                {group}                       AS bucket,
                COUNT(*)                      AS requests,
                SUM(prompt_tokens)            AS prompt_tokens_sum,
                SUM(completion_tokens)        AS completion_tokens_sum,
                SUM(total_tokens)             AS total_tokens_sum,
                AVG(latency_ms)               AS latency_ms_avg,
                SUM(cost_usd)                 AS cost_usd_sum,
                SUM(status = 'error')         AS errors
            FROM requests
            {where}
            GROUP BY bucket
            ORDER BY cost_usd_sum DESC, total_tokens_sum DESC
        """
        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_agg(r) for r in rows]

    def top(
        self,
        metric: str = "cost",
        limit: int = 10,
        by: str = "model",
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        """Biggest consumers grouped by model (or backend), ranked by metric."""
        if metric not in _TOP_METRIC:
            raise ValueError(f"unknown metric: {metric!r} (use cost|tokens|requests)")
        rows = self.aggregate(by=by, since=since, until=until)
        rows.sort(key=lambda r: r[_TOP_METRIC[metric]], reverse=True)
        return rows[:limit]

    def records(
        self, since: str | None = None, until: str | None = None
    ) -> list[dict]:
        """Raw rows in range, oldest first -- used by the JSON/CSV export."""
        where, params = _time_clause(since, until)
        sql = f"""
            SELECT request_id, ts, model, backend, prompt_tokens, completion_tokens,
                   total_tokens, latency_ms, cost_usd, status, source
            FROM requests
            {where}
            ORDER BY ts ASC, id ASC
        """
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]


def _time_clause(since: str | None, until: str | None) -> tuple[str, list]:
    clauses, params = [], []
    if since:
        clauses.append("ts >= ?")
        params.append(since)
    if until:
        clauses.append("ts <= ?")
        params.append(until)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def _row_to_agg(row: sqlite3.Row) -> dict:
    return {
        "bucket": row["bucket"],
        "requests": row["requests"] or 0,
        "prompt_tokens_sum": row["prompt_tokens_sum"] or 0,
        "completion_tokens_sum": row["completion_tokens_sum"] or 0,
        "total_tokens_sum": row["total_tokens_sum"] or 0,
        "latency_ms_avg": (
            round(row["latency_ms_avg"], 2) if row["latency_ms_avg"] is not None else None
        ),
        "cost_usd_sum": round(row["cost_usd_sum"] or 0.0, 6),
        "errors": row["errors"] or 0,
    }

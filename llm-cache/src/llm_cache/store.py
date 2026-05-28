"""SQLite-backed cache store.

Schema:
  entries(key TEXT PRIMARY KEY, bucket TEXT, body BLOB, content_type TEXT,
          created_at REAL, expires_at REAL, last_hit REAL, hit_count INTEGER,
          embedding BLOB, prompt TEXT, byte_size INTEGER)

`embedding` and `prompt` are populated only for semantic-mode chat entries.
"""

from __future__ import annotations

import math
import sqlite3
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class CacheEntry:
    key: str
    bucket: str
    body: bytes
    content_type: str
    created_at: float
    expires_at: float
    last_hit: float
    hit_count: int
    prompt: Optional[str] = None
    embedding: Optional[list[float]] = None
    byte_size: int = 0


def _pack_vec(vec: Iterable[float]) -> bytes:
    arr = list(vec)
    return struct.pack(f"<{len(arr)}f", *arr)


def _unpack_vec(blob: bytes | None) -> Optional[list[float]]:
    if not blob:
        return None
    count = len(blob) // 4
    return list(struct.unpack(f"<{count}f", blob))


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


class CacheStore:
    """Thread-safe-ish SQLite store. The connection uses WAL and check_same_thread=False
    so the FastAPI worker can share it across the threadpool used by httpx sync calls."""

    def __init__(self, path: Path, ttl_seconds: int, max_entries: int):
        self.path = Path(path)
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                key TEXT PRIMARY KEY,
                bucket TEXT NOT NULL,
                body BLOB NOT NULL,
                content_type TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                last_hit REAL NOT NULL,
                hit_count INTEGER NOT NULL DEFAULT 0,
                prompt TEXT,
                embedding BLOB,
                byte_size INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entries_bucket ON entries(bucket)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entries_last_hit ON entries(last_hit)"
        )

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ ops

    def get(self, key: str, now: float | None = None) -> Optional[CacheEntry]:
        now = now if now is not None else time.time()
        row = self._conn.execute(
            "SELECT key, bucket, body, content_type, created_at, expires_at, "
            "last_hit, hit_count, prompt, embedding, byte_size "
            "FROM entries WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        if row[5] <= now:
            self.delete(key)
            return None
        self._conn.execute(
            "UPDATE entries SET last_hit = ?, hit_count = hit_count + 1 WHERE key = ?",
            (now, key),
        )
        return CacheEntry(
            key=row[0],
            bucket=row[1],
            body=row[2],
            content_type=row[3],
            created_at=row[4],
            expires_at=row[5],
            last_hit=now,
            hit_count=row[7] + 1,
            prompt=row[8],
            embedding=_unpack_vec(row[9]),
            byte_size=row[10],
        )

    def put(
        self,
        key: str,
        bucket: str,
        body: bytes,
        content_type: str,
        prompt: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        now: float | None = None,
    ) -> None:
        now = now if now is not None else time.time()
        expires = now + self.ttl_seconds
        self._conn.execute(
            "INSERT OR REPLACE INTO entries "
            "(key, bucket, body, content_type, created_at, expires_at, last_hit, "
            " hit_count, prompt, embedding, byte_size) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                key,
                bucket,
                body,
                content_type,
                now,
                expires,
                now,
                0,
                prompt,
                _pack_vec(embedding) if embedding is not None else None,
                len(body),
            ),
        )
        self._evict_if_needed()

    def delete(self, key: str) -> bool:
        cur = self._conn.execute("DELETE FROM entries WHERE key = ?", (key,))
        return cur.rowcount > 0

    def purge_expired(self, now: float | None = None) -> int:
        now = now if now is not None else time.time()
        cur = self._conn.execute("DELETE FROM entries WHERE expires_at <= ?", (now,))
        return cur.rowcount or 0

    def purge_all(self) -> int:
        cur = self._conn.execute("DELETE FROM entries")
        return cur.rowcount or 0

    def _evict_if_needed(self) -> None:
        row = self._conn.execute("SELECT COUNT(*) FROM entries").fetchone()
        count = row[0] if row else 0
        if count <= self.max_entries:
            return
        over = count - self.max_entries
        self._conn.execute(
            "DELETE FROM entries WHERE key IN ("
            "SELECT key FROM entries ORDER BY last_hit ASC LIMIT ?"
            ")",
            (over,),
        )

    # --------------------------------------------------------- semantic search

    def semantic_lookup(
        self,
        bucket: str,
        query: list[float],
        threshold: float,
        now: float | None = None,
    ) -> Optional[tuple[CacheEntry, float]]:
        now = now if now is not None else time.time()
        best: tuple[CacheEntry, float] | None = None
        cur = self._conn.execute(
            "SELECT key, bucket, body, content_type, created_at, expires_at, "
            "last_hit, hit_count, prompt, embedding, byte_size "
            "FROM entries WHERE bucket = ? AND embedding IS NOT NULL "
            "AND expires_at > ?",
            (bucket, now),
        )
        for row in cur.fetchall():
            vec = _unpack_vec(row[9])
            if vec is None:
                continue
            sim = cosine(query, vec)
            if sim >= threshold and (best is None or sim > best[1]):
                entry = CacheEntry(
                    key=row[0],
                    bucket=row[1],
                    body=row[2],
                    content_type=row[3],
                    created_at=row[4],
                    expires_at=row[5],
                    last_hit=row[6],
                    hit_count=row[7],
                    prompt=row[8],
                    embedding=vec,
                    byte_size=row[10],
                )
                best = (entry, sim)
        if best is None:
            return None
        # Bump hit stats on the winning row.
        self._conn.execute(
            "UPDATE entries SET last_hit = ?, hit_count = hit_count + 1 WHERE key = ?",
            (now, best[0].key),
        )
        winner = best[0]
        winner.last_hit = now
        winner.hit_count += 1
        return winner, best[1]

    # ------------------------------------------------------------------ stats

    def stats(self) -> dict[str, int]:
        row = self._conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(byte_size), 0), COALESCE(SUM(hit_count), 0) "
            "FROM entries"
        ).fetchone()
        return {
            "entries": row[0] or 0,
            "bytes_stored": row[1] or 0,
            "total_hits": row[2] or 0,
        }

    def iter_all(self) -> Iterable[CacheEntry]:
        cur = self._conn.execute(
            "SELECT key, bucket, body, content_type, created_at, expires_at, "
            "last_hit, hit_count, prompt, embedding, byte_size FROM entries"
        )
        for row in cur.fetchall():
            yield CacheEntry(
                key=row[0],
                bucket=row[1],
                body=row[2],
                content_type=row[3],
                created_at=row[4],
                expires_at=row[5],
                last_hit=row[6],
                hit_count=row[7],
                prompt=row[8],
                embedding=_unpack_vec(row[9]),
                byte_size=row[10],
            )

"""In-process metrics for cache hits, misses and savings estimates."""

from __future__ import annotations

import threading
from dataclasses import asdict, dataclass


@dataclass
class Metrics:
    hits_exact: int = 0
    hits_semantic: int = 0
    misses: int = 0
    bypasses: int = 0
    refreshes: int = 0
    upstream_errors: int = 0
    bytes_saved: int = 0
    tokens_saved_estimate: int = 0


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._m = Metrics()

    def hit_exact(self, body_len: int) -> None:
        with self._lock:
            self._m.hits_exact += 1
            self._m.bytes_saved += body_len
            self._m.tokens_saved_estimate += _estimate_tokens(body_len)

    def hit_semantic(self, body_len: int) -> None:
        with self._lock:
            self._m.hits_semantic += 1
            self._m.bytes_saved += body_len
            self._m.tokens_saved_estimate += _estimate_tokens(body_len)

    def miss(self) -> None:
        with self._lock:
            self._m.misses += 1

    def bypass(self) -> None:
        with self._lock:
            self._m.bypasses += 1

    def refresh(self) -> None:
        with self._lock:
            self._m.refreshes += 1

    def upstream_error(self) -> None:
        with self._lock:
            self._m.upstream_errors += 1

    def snapshot(self) -> dict:
        with self._lock:
            data = asdict(self._m)
        total = data["hits_exact"] + data["hits_semantic"] + data["misses"]
        data["total_requests"] = total
        data["hit_rate"] = (
            (data["hits_exact"] + data["hits_semantic"]) / total if total else 0.0
        )
        return data


def _estimate_tokens(byte_len: int) -> int:
    """Rough estimate: ~4 chars per token, response bytes approx == chars (ASCII-ish)."""
    if byte_len <= 0:
        return 0
    return max(1, byte_len // 4)

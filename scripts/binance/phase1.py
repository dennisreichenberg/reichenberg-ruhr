"""Phase-1 clean-cycle counter and auto-pause logic (REI-329 Gate 3).

State file: data/treasury/phase1_clean_cycles.json
Tracks clean_count, consecutive_failures, and the 14-day window.

A cycle is "clean" when all four stages complete:
1. API fetch + permission check (Gate 1)
2. Strategy run without sanity-bound violation (Gate 2)
3. Snapshot + paper_trades written to storage
4. Audit comment posted to Trading-Log

Consecutive failures >= 2 triggers auto-pause of the Paperclip routine
via PATCH /api/routines/{ROUTINE_ID}.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal

ROUTINE_ID = "4f79c706-9333-44ce-b2be-b7b9b0950101"
PHASE1_REQUIRED_CLEAN = 14
MAX_CONSECUTIVE_FAILURES = 2


@dataclass
class Phase1State:
    started_at: str = ""
    clean_count: int = 0
    total_count: int = 0
    consecutive_failures: int = 0
    last_clean_date: str = ""
    last_run_date: str = ""
    routine_auto_paused: bool = False
    history: list = field(default_factory=list)

    def record_clean(self, run_date: date) -> None:
        self.clean_count += 1
        self.total_count += 1
        self.consecutive_failures = 0
        self.last_clean_date = run_date.isoformat()
        self.last_run_date = run_date.isoformat()
        self.history.append({"date": run_date.isoformat(), "result": "clean"})

    def record_failure(self, run_date: date, reason: str) -> None:
        self.total_count += 1
        self.consecutive_failures += 1
        self.last_run_date = run_date.isoformat()
        self.history.append({"date": run_date.isoformat(), "result": "failed", "reason": reason})

    @property
    def phase1_complete(self) -> bool:
        return self.clean_count >= PHASE1_REQUIRED_CLEAN

    @property
    def should_auto_pause(self) -> bool:
        return self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES and not self.routine_auto_paused


def load(state_path: Path) -> Phase1State:
    if not state_path.exists():
        s = Phase1State(started_at=datetime.now(timezone.utc).isoformat())
        return s
    data = json.loads(state_path.read_text(encoding="utf-8"))
    return Phase1State(**{k: data.get(k, v) for k, v in asdict(Phase1State()).items()})


def save(state: Phase1State, state_path: Path) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False), encoding="utf-8")


def pause_routine(routine_id: str = ROUTINE_ID) -> bool:
    """PATCH the Paperclip routine to enabled=false.

    Uses PAPERCLIP_API_URL + PAPERCLIP_API_TOKEN env vars if set,
    otherwise falls back to localhost:3737.
    Returns True if the PATCH succeeded.
    """
    try:
        import urllib.request, urllib.parse
        base_url = os.environ.get("PAPERCLIP_API_URL", "http://localhost:3737")
        token = os.environ.get("PAPERCLIP_API_TOKEN", "")
        url = f"{base_url}/api/routines/{routine_id}"
        payload = json.dumps({"enabled": False}).encode()
        req = urllib.request.Request(url, data=payload, method="PATCH")
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 300
    except Exception:
        return False

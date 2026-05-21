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


def _paperclip_auth() -> tuple[str, str]:
    """Return (base_url, bearer_token) for Paperclip REST calls.

    Reads PAPERCLIP_API_URL (default http://localhost:3100) and the bearer
    from PAPERCLIP_API_TOKEN or PAPERCLIP_API_KEY (Backend-Agent adapter env
    uses the latter; both are accepted so the script works in either context).
    """
    base_url = os.environ.get("PAPERCLIP_API_URL", "http://localhost:3100")
    token = os.environ.get("PAPERCLIP_API_TOKEN") or os.environ.get("PAPERCLIP_API_KEY", "")
    return base_url, token


TRADING_LOG_ISSUE_ID = "f06362be-4b2c-4e4d-aab3-326a03dbbad6"


def post_audit_comment(
    run_date: date,
    result: str,
    gate1_ok: bool,
    gate2_max_pct: float,
    state: "Phase1State",
    digest_ok: bool,
    error: str = "",
    issue_id: str = TRADING_LOG_ISSUE_ID,
) -> bool:
    """POST a cycle audit comment to the Trading-Log issue (REI-330).

    Returns True if the HTTP call succeeded (2xx). On failure: returns False
    without raising so the caller can decide whether to mark the cycle as failed.
    """
    try:
        import urllib.request
        base_url, token = _paperclip_auth()
        url = f"{base_url}/api/issues/{issue_id}/comments"

        lines = [
            f"Cycle {run_date.isoformat()} [phase=read_only] result={result}",
            f"Gate1(permissions): {'OK' if gate1_ok else 'FAIL'}",
            f"Gate2(sanity): max_trade={gate2_max_pct:.1f}%",
            f"Gate3(counter): {state.clean_count}/{PHASE1_REQUIRED_CLEAN} clean "
            f"(total={state.total_count}, consecutive_failures={state.consecutive_failures})",
            f"DigestWrite: {'OK' if digest_ok else 'FAIL'}",
        ]
        if error:
            lines.append(f"Error: {error}")

        body = json.dumps({"body": "\n".join(lines)}).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status < 300
    except Exception:
        return False


def pause_routine(routine_id: str = ROUTINE_ID) -> bool:
    """PATCH the Paperclip routine to status=paused.

    Returns True if the PATCH succeeded AND the routine actually moved
    out of `active`. A 200 response alone is not sufficient because the
    server silently no-ops on unknown fields (`{"enabled": false}` returns
    200 but leaves status unchanged -- only `{"status": "paused"}` works).
    """
    try:
        import urllib.request
        base_url, token = _paperclip_auth()
        url = f"{base_url}/api/routines/{routine_id}"
        payload = json.dumps({"status": "paused"}).encode()
        req = urllib.request.Request(url, data=payload, method="PATCH")
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status >= 300:
                return False
            body = json.loads(resp.read().decode() or "{}")
            return body.get("status") == "paused"
    except Exception:
        return False

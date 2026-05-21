"""Main cycle entry point: pull -> snapshot -> strategy -> digest.

Invoked by:
    python -m scripts.binance.cycle [--fixtures scripts/binance/fixtures] [--date YYYY-MM-DD]

Phase 1: never sends an order, never withdraws. Gates 1-3 enforced per run.
"""

from __future__ import annotations

import argparse
import json
import os
import traceback
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from . import PHASE
from .client import BinanceClient, Credentials
from .config import ASSETS, QUOTE, load as load_config
from .digest import build as build_digest
from . import phase1 as p1
from .portfolio import buy_and_hold_baseline, derive_eur_portfolio
from .strategy import decide


REPO_ROOT = Path(__file__).resolve().parents[2]

# Allow overriding data dir via env for persistent-across-worktrees storage (REI-332)
DATA_DIR = Path(os.environ.get("BINANCE_DATA_DIR", str(REPO_ROOT / "data" / "treasury")))
SECRETS_FILE = REPO_ROOT / "secrets" / "binance.json"
STATE_FILE = DATA_DIR / "phase1_clean_cycles.json"

# Gate 1: hard-coded expected account snapshot taken 2026-05-21 (sniffed from live call)
EXPECTED_ACCOUNT_TYPE = "SPOT"
EXPECTED_PERMISSIONS = ["TRD_GRP_046"]


class CycleGateError(RuntimeError):
    """Raised when a Phase-1 gate is violated; cycle must abort."""


def _gate1_permissions(account: dict) -> None:
    """Abort if account type or permission group has changed since setup."""
    account_type = account.get("accountType")
    permissions = sorted(account.get("permissions", []))
    if account_type != EXPECTED_ACCOUNT_TYPE:
        raise CycleGateError(
            f"Gate1 FAIL: accountType changed from {EXPECTED_ACCOUNT_TYPE!r} to {account_type!r}. "
            "Key may have been rotated or upgraded."
        )
    if permissions != sorted(EXPECTED_PERMISSIONS):
        raise CycleGateError(
            f"Gate1 FAIL: permissions changed from {EXPECTED_PERMISSIONS} to {permissions}. "
            "Key may have been upgraded to trading permissions."
        )


def _gate2_sanity_bound(paper_trades: list, portfolio_total_eur: float) -> None:
    """Abort if any single paper-trade exceeds 10% of total portfolio."""
    if portfolio_total_eur <= 0:
        return
    cap = portfolio_total_eur * 0.10
    for t in paper_trades:
        if t.eur_amount > cap:
            raise CycleGateError(
                f"Gate2 FAIL: paper trade {t.side} {t.asset} {t.eur_amount:.2f} EUR "
                f"exceeds 10% cap ({cap:.2f} EUR) on portfolio {portfolio_total_eur:.2f} EUR. "
                f"Component={t.component} reason={t.reason!r}"
            )


def _load_history() -> list[dict]:
    if not DATA_DIR.exists():
        return []
    snapshots = sorted(DATA_DIR.glob("snapshot-*.json"))
    return [json.loads(p.read_text(encoding="utf-8")) for p in snapshots]


def _write_snapshot(snapshot: dict) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"snapshot-{snapshot['date'].replace('-', '')}.json"
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _append_paper_trades(trades: list) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "paper_trades.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        for t in trades:
            fh.write(t.to_jsonl() + "\n")
    return path


def _kline_closes(klines: list[list]) -> list[float]:
    return [float(k[4]) for k in klines]


def run(fixtures_dir: Path | None, run_date: date) -> dict:
    assert PHASE == "read_only", f"Refusing to run in PHASE={PHASE!r} without explicit phase-2 sign-off"
    cfg = load_config()
    state = p1.load(STATE_FILE)

    # ── Stage 1: fetch ──────────────────────────────────────────────────────
    if fixtures_dir is not None:
        client = BinanceClient(fixtures_dir=fixtures_dir)
    else:
        if not SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"{SECRETS_FILE} missing. Either provide a real key (REI-329 gate) "
                "or pass --fixtures scripts/binance/fixtures"
            )
        client = BinanceClient(credentials=Credentials.from_file(SECRETS_FILE))

    account = client.get_account()

    # Gate 1: permission check (skip in fixture mode)
    if fixtures_dir is None:
        _gate1_permissions(account)

    tickers: dict[str, float] = {}
    for a in ASSETS:
        tickers[f"{a}{QUOTE}"] = float(client.get_symbol_ticker(f"{a}{QUOTE}")["price"])
    if fixtures_dir is None:
        for stable, eur_pair in (("USDT", "EURUSDT"), ("USDC", "EURUSDC")):
            try:
                eur_price = float(client.get_symbol_ticker(eur_pair)["price"])
                tickers[f"{stable}{QUOTE}"] = 1.0 / eur_price
            except Exception:
                pass

    portfolio_eur = derive_eur_portfolio(account, tickers)

    quantities = {}
    for bal in account.get("balances", []):
        qty = float(bal["free"]) + float(bal["locked"])
        if qty > 0:
            quantities[bal["asset"]] = qty

    klines_by_asset = {a: client.get_klines(f"{a}{QUOTE}", interval="1d", limit=400) for a in ASSETS}
    prices_by_asset = {a: _kline_closes(klines_by_asset[a]) for a in ASSETS}

    # ── Stage 2: strategy ───────────────────────────────────────────────────
    paper_trades = decide(
        portfolio_eur=portfolio_eur,
        prices_by_asset=prices_by_asset,
        daily_eur_spent=0.0,
        cfg=cfg,
        today=run_date,
    )

    # Gate 2: sanity bound (skip in fixture mode)
    if fixtures_dir is None:
        portfolio_total = sum(portfolio_eur.values())
        _gate2_sanity_bound(paper_trades, portfolio_total)

    # ── Stage 3: persist ────────────────────────────────────────────────────
    _append_paper_trades(paper_trades)

    history = _load_history()
    snapshot = {
        "date": run_date.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": PHASE,
        "prices": tickers,
        "quantities": quantities,
        "eur_balances": {QUOTE: portfolio_eur.get(QUOTE, 0.0)},
        "eur_portfolio": portfolio_eur,
        "paper_pnl_eur": _compute_paper_pnl(history, paper_trades),
        "buy_and_hold_delta_pct": buy_and_hold_baseline(history)["delta_pct"] if history else 0.0,
    }
    _write_snapshot(snapshot)

    history_with_current = history + [snapshot]
    digest = build_digest(snapshot, [asdict(t) for t in paper_trades], history_with_current)
    digest_path = DATA_DIR / f"digest-{snapshot['date'].replace('-', '')}.json"
    digest_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")

    result = {
        "snapshot": snapshot,
        "digest": digest,
        "paper_trades": [asdict(t) for t in paper_trades],
    }

    # ── Stage 4: state-file update (Gate 3 counter) ─────────────────────────
    # Audit-comment posting (Stage 4) is handled by the caller (main()) so that
    # we can mark clean only after the comment actually succeeds.
    result["_state"] = state
    result["_run_date"] = run_date
    return result


def _mark_cycle_outcome(state: p1.Phase1State, run_date: date, success: bool, reason: str = "") -> None:
    if success:
        state.record_clean(run_date)
    else:
        state.record_failure(run_date, reason)
    p1.save(state, STATE_FILE)

    if state.should_auto_pause:
        paused = p1.pause_routine()
        if paused:
            state.routine_auto_paused = True
            p1.save(state, STATE_FILE)


def _compute_paper_pnl(history: list[dict], todays_trades: list) -> float:
    return round(sum(t.eur_amount for t in todays_trades if t.approved and t.side == "buy") -
                 sum(t.eur_amount for t in todays_trades if t.approved and t.side == "sell"), 2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Binance Phase-1 shadow cycle")
    parser.add_argument("--fixtures", type=Path, default=None,
                        help="Directory containing account/my_trades/klines fixtures")
    parser.add_argument("--date", type=str, default=None,
                        help="Override run date (YYYY-MM-DD)")
    parser.add_argument("--print-digest", action="store_true",
                        help="Print the digest text to stdout")
    args = parser.parse_args(argv)

    run_date = date.fromisoformat(args.date) if args.date else date.today()
    fixtures = args.fixtures
    if fixtures is None and os.environ.get("BINANCE_FIXTURES"):
        fixtures = Path(os.environ["BINANCE_FIXTURES"])

    state: p1.Phase1State | None = None
    try:
        result = run(fixtures_dir=fixtures, run_date=run_date)
        state = result.pop("_state")
        run_date_obj = result.pop("_run_date")

        if args.print_digest:
            print(result["digest"]["telegram_text"])

        # ── Stage 4: audit comment + clean-cycle counter ─────────────────────
        if fixtures is None:
            portfolio_total = sum(result["snapshot"].get("eur_portfolio", {}).values())
            trades = result["paper_trades"]
            gate2_max_pct = (max((t["eur_amount"] for t in trades), default=0.0) / portfolio_total * 100
                             if portfolio_total > 0 else 0.0)
            digest_ok = "telegram_text" in result.get("digest", {})

            # Post audit comment to REI-330 BEFORE marking clean.
            # If the comment POST fails, count the cycle as failed (Gate 3 Stage 4).
            comment_ok = p1.post_audit_comment(
                run_date=run_date_obj,
                result="clean",
                gate1_ok=True,
                gate2_max_pct=gate2_max_pct,
                state=state,
                digest_ok=digest_ok,
            )
            if comment_ok:
                _mark_cycle_outcome(state, run_date_obj, success=True)
            else:
                _mark_cycle_outcome(state, run_date_obj, success=False,
                                    reason="Stage4: audit comment POST to REI-330 failed")

        clean = state.clean_count
        print(f"Phase-1 clean cycles: {clean}/{p1.PHASE1_REQUIRED_CLEAN}")
        return 0 if (fixtures is not None or state.history[-1]["result"] == "clean") else 1

    except CycleGateError as exc:
        err_msg = str(exc)
        print(f"GATE VIOLATION: {err_msg}", flush=True)
        if state is None:
            state = p1.load(STATE_FILE)
        _mark_cycle_outcome(state, run_date, success=False, reason=err_msg)
        if fixtures is None:
            p1.post_audit_comment(run_date=run_date, result="failed", gate1_ok=False,
                                  gate2_max_pct=0.0, state=state, digest_ok=False, error=err_msg)
        if state.routine_auto_paused:
            print("Routine auto-paused due to consecutive failures.")
        return 2

    except Exception as exc:
        err_msg = repr(exc)
        print(f"CYCLE FAILED: {err_msg}", flush=True)
        traceback.print_exc()
        if state is None:
            state = p1.load(STATE_FILE)
        _mark_cycle_outcome(state, run_date, success=False, reason=err_msg)
        if fixtures is None:
            p1.post_audit_comment(run_date=run_date, result="failed", gate1_ok=False,
                                  gate2_max_pct=0.0, state=state, digest_ok=False, error=err_msg)
        if state.routine_auto_paused:
            print("Routine auto-paused due to consecutive failures.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

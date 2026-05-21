"""Main cycle entry point: pull -> snapshot -> strategy -> digest.

Invoked by:
    python -m scripts.binance.cycle [--fixtures scripts/binance/fixtures] [--date YYYY-MM-DD]

Phase 1: never sends an order, never withdraws.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from . import PHASE
from .client import BinanceClient, Credentials
from .config import ASSETS, QUOTE, load as load_config
from .digest import build as build_digest
from .portfolio import buy_and_hold_baseline, derive_eur_portfolio
from .strategy import decide


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "treasury"
SECRETS_FILE = REPO_ROOT / "secrets" / "binance.json"


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
    tickers: dict[str, float] = {}
    for a in ASSETS:
        tickers[f"{a}{QUOTE}"] = float(client.get_symbol_ticker(f"{a}{QUOTE}")["price"])
    # Stablecoin → EUR rates via inverted EUR/USD pairs (EURUSDT, EURUSDC exist on Binance)
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

    paper_trades = decide(
        portfolio_eur=portfolio_eur,
        prices_by_asset=prices_by_asset,
        daily_eur_spent=0.0,
        cfg=cfg,
        today=run_date,
    )
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
        "paper_pnl_eur": _compute_paper_pnl(history + [{}], paper_trades),
        "buy_and_hold_delta_pct": buy_and_hold_baseline(history)["delta_pct"] if history else 0.0,
    }
    _write_snapshot(snapshot)

    history_with_current = history + [snapshot]
    digest = build_digest(snapshot, [asdict(t) for t in paper_trades], history_with_current)
    digest_path = DATA_DIR / f"digest-{snapshot['date'].replace('-', '')}.json"
    digest_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "snapshot": snapshot,
        "digest": digest,
        "paper_trades": [asdict(t) for t in paper_trades],
    }


def _compute_paper_pnl(history: list[dict], todays_trades: list) -> float:
    """Crude paper-PnL: sum of approved buy notionals stays flat; we revalue
    later when more snapshots accumulate. Real PnL math lands in the weekly
    report once we have >7 snapshots."""
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

    result = run(fixtures_dir=fixtures, run_date=run_date)
    if args.print_digest:
        print(result["digest"]["telegram_text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

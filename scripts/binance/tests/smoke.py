"""Smoke test for the Binance shadow cycle.

Invoke as:
    python -m scripts.binance.tests.smoke

The point is to fail loudly if any of the Phase-1 guarantees regresses:
- order endpoint must raise
- withdraw endpoint must raise
- risk rails fire when budget/limit is exceeded
- strategy is deterministic across two runs
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from scripts.binance import PHASE
from scripts.binance.client import BinanceClient, PhaseError
from scripts.binance.config import load as load_config
from scripts.binance.cycle import run
from scripts.binance.risk import TradeProposal, evaluate
from scripts.binance.strategy import decide


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _fail(msg: str) -> None:
    print(f"FAIL  {msg}", file=sys.stderr)
    sys.exit(1)


def test_phase_constant() -> None:
    assert PHASE == "read_only", f"PHASE must be read_only, got {PHASE!r}"
    print("OK    phase constant is read_only")


def test_order_disabled() -> None:
    client = BinanceClient(fixtures_dir=FIXTURES)
    try:
        client.place_order(symbol="BTCEUR", side="BUY", type="MARKET", quantity=0.001)
    except PhaseError as e:
        print(f"OK    place_order rejected: {e}")
    else:
        _fail("place_order did NOT raise PhaseError")
    try:
        client.withdraw(coin="BTC", amount=0.001, address="x")
    except PhaseError as e:
        print(f"OK    withdraw rejected: {e}")
    else:
        _fail("withdraw did NOT raise PhaseError")


def test_risk_daily_budget() -> None:
    cfg = load_config()
    proposal = TradeProposal(side="buy", asset="BTC", eur_amount=500.0, reason="x")
    decision = evaluate(proposal, {"BTC": 1000.0, "EUR": 200.0}, daily_eur_spent=50.0, cfg=cfg)
    if "daily_budget_clamp" not in decision.rails_triggered:
        _fail(f"expected daily_budget_clamp, got {decision.rails_triggered}")
    if decision.eur_amount > cfg.daily_budget_eur:
        _fail(f"clamped amount exceeds budget: {decision.eur_amount}")
    print(f"OK    risk daily-budget rail: {decision.rails_triggered}, eur={decision.eur_amount}")


def test_risk_position_limit() -> None:
    cfg = load_config()
    # Already 900 EUR in BTC out of 1000; trying to add 500 should clamp
    proposal = TradeProposal(side="buy", asset="BTC", eur_amount=80.0, reason="x")
    decision = evaluate(proposal, {"BTC": 900.0, "EUR": 100.0}, daily_eur_spent=0.0, cfg=cfg)
    if "max_position_clamp" not in decision.rails_triggered:
        _fail(f"expected max_position_clamp, got {decision.rails_triggered}")
    print(f"OK    risk position-limit rail: {decision.rails_triggered}, eur={decision.eur_amount}")


def test_strategy_deterministic() -> None:
    cfg = load_config()
    portfolio = {"BTC": 5300.0, "ETH": 4300.0, "BNB": 1100.0, "EUR": 320.0}
    # Build a price ladder long enough to trigger SMA logic
    import math
    prices = {a: [50000 * (1 + 0.001*i + 0.04*math.sin(i/15.0)) for i in range(250)] for a in ("BTC", "ETH", "BNB")}
    out1 = decide(portfolio, prices, daily_eur_spent=0.0, cfg=cfg, today=date(2026, 6, 1))
    out2 = decide(portfolio, prices, daily_eur_spent=0.0, cfg=cfg, today=date(2026, 6, 1))
    if [t.to_jsonl() for t in out1] != [t.to_jsonl() for t in out2]:
        _fail("strategy is not deterministic")
    print(f"OK    strategy deterministic, produced {len(out1)} trades")


def test_full_cycle_with_fixtures(tmp: Path) -> None:
    import scripts.binance.cycle as cycle_mod
    original_data_dir = cycle_mod.DATA_DIR
    cycle_mod.DATA_DIR = tmp
    try:
        result = run(fixtures_dir=FIXTURES, run_date=date(2026, 6, 1))
    finally:
        cycle_mod.DATA_DIR = original_data_dir

    snap = result["snapshot"]
    if snap["phase"] != "read_only":
        _fail(f"snapshot phase wrong: {snap['phase']}")
    if not snap["eur_portfolio"]:
        _fail("eur_portfolio empty")
    if "telegram_text" not in result["digest"]:
        _fail("digest missing telegram_text")
    print("OK    full cycle ran, snapshot phase=read_only, digest produced")
    print("---- DIGEST TEXT ----")
    print(result["digest"]["telegram_text"])
    print("---------------------")


def main() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_phase_constant()
        test_order_disabled()
        test_risk_daily_budget()
        test_risk_position_limit()
        test_strategy_deterministic()
        test_full_cycle_with_fixtures(tmp)
        print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()

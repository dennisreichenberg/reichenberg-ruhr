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
from scripts.binance.cycle import CycleGateError, _gate1_permissions, _gate2_sanity_bound, EXPECTED_ACCOUNT_TYPE, EXPECTED_PERMISSIONS
from scripts.binance import phase1 as p1
from scripts.binance.strategy import PaperTrade
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


def test_gate1_permissions() -> None:
    # Valid account → no raise
    valid = {"accountType": EXPECTED_ACCOUNT_TYPE, "permissions": EXPECTED_PERMISSIONS}
    try:
        _gate1_permissions(valid)
        print(f"OK    gate1 passes on correct account type + permissions")
    except CycleGateError as e:
        _fail(f"gate1 raised on valid account: {e}")

    # Wrong type → raise
    wrong_type = {"accountType": "MARGIN", "permissions": EXPECTED_PERMISSIONS}
    try:
        _gate1_permissions(wrong_type)
        _fail("gate1 did not raise on wrong accountType")
    except CycleGateError as e:
        print(f"OK    gate1 rejects wrong accountType: {str(e)[:60]}")

    # Extra permission → raise
    extra_perm = {"accountType": EXPECTED_ACCOUNT_TYPE, "permissions": EXPECTED_PERMISSIONS + ["TRADE_ENABLED"]}
    try:
        _gate1_permissions(extra_perm)
        _fail("gate1 did not raise on extra permission")
    except CycleGateError as e:
        print(f"OK    gate1 rejects extra permissions: {str(e)[:60]}")


def test_gate2_sanity_bound() -> None:
    # Trade at 9% → OK
    trade_ok = PaperTrade("2026-06-01", "buy", "BTC", 9.0, "sma", "sma cross", [], True)
    try:
        _gate2_sanity_bound([trade_ok], 100.0)
        print("OK    gate2 allows 9% trade on 100 EUR portfolio")
    except CycleGateError:
        _fail("gate2 raised on 9% trade (should be under cap)")

    # Trade at 11% → fail
    trade_over = PaperTrade("2026-06-01", "buy", "BTC", 11.0, "sma", "sma cross", [], True)
    try:
        _gate2_sanity_bound([trade_over], 100.0)
        _fail("gate2 did not raise on 11% trade")
    except CycleGateError as e:
        print(f"OK    gate2 rejects 11% trade: {str(e)[:60]}")


def test_gate3_state_file() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        from datetime import date
        state_path = Path(td) / "phase1_clean_cycles.json"

        state = p1.load(state_path)
        assert state.clean_count == 0
        assert state.consecutive_failures == 0

        for i in range(3):
            state.record_clean(date(2026, 6, i + 1))
        p1.save(state, state_path)
        reloaded = p1.load(state_path)
        assert reloaded.clean_count == 3, f"expected 3, got {reloaded.clean_count}"

        state.record_failure(date(2026, 6, 4), "test failure 1")
        assert state.consecutive_failures == 1
        assert not state.should_auto_pause

        state.record_failure(date(2026, 6, 5), "test failure 2")
        assert state.consecutive_failures == 2
        assert state.should_auto_pause

        print("OK    gate3 state file: clean counter, failure counter, auto-pause trigger")


def test_full_cycle_with_fixtures(tmp: Path) -> None:
    import scripts.binance.cycle as cycle_mod
    original_data_dir = cycle_mod.DATA_DIR
    original_state_file = cycle_mod.STATE_FILE
    cycle_mod.DATA_DIR = tmp
    cycle_mod.STATE_FILE = tmp / "phase1_clean_cycles.json"
    try:
        result = run(fixtures_dir=FIXTURES, run_date=date(2026, 6, 1))
    finally:
        cycle_mod.DATA_DIR = original_data_dir
        cycle_mod.STATE_FILE = original_state_file

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
        test_gate1_permissions()
        test_gate2_sanity_bound()
        test_gate3_state_file()
        test_full_cycle_with_fixtures(tmp)
        print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()

"""Portfolio derivation from a Binance /api/v3/account response."""

from __future__ import annotations

from .config import ASSETS, QUOTE


def derive_eur_portfolio(account: dict, tickers: dict[str, float]) -> dict[str, float]:
    """Return EUR-denominated holdings keyed by asset.

    `tickers` maps SYMBOL -> price float (e.g. {"BTCEUR": 65000.0}).
    Stable balances are included at their face value (treated as ~1 EUR).
    """
    holdings: dict[str, float] = {}
    for bal in account.get("balances", []):
        asset = bal["asset"]
        total = float(bal["free"]) + float(bal["locked"])
        if total <= 0:
            continue
        if asset == QUOTE:
            holdings[asset] = holdings.get(asset, 0.0) + total
            continue
        symbol = f"{asset}{QUOTE}"
        price = tickers.get(symbol)
        if price is None:
            continue
        holdings[asset] = holdings.get(asset, 0.0) + total * price
    return holdings


def buy_and_hold_baseline(snapshot_history: list[dict]) -> dict:
    """Project the EUR value if all initial holdings stayed put.

    `snapshot_history` is the ordered list of daily snapshot dicts. The
    first entry's per-asset quantities are revalued at the latest price.
    """
    if not snapshot_history:
        return {"baseline_eur": 0.0, "delta_pct": 0.0}

    first = snapshot_history[0]
    last = snapshot_history[-1]

    baseline = 0.0
    for asset in ASSETS:
        qty = first.get("quantities", {}).get(asset, 0.0)
        price = last.get("prices", {}).get(f"{asset}{QUOTE}", 0.0)
        baseline += qty * price
    baseline += first.get("eur_balances", {}).get(QUOTE, 0.0)

    current_total = sum(last.get("eur_portfolio", {}).values())
    delta_pct = ((current_total - baseline) / baseline * 100) if baseline > 0 else 0.0
    return {"baseline_eur": round(baseline, 2), "delta_pct": round(delta_pct, 2)}

"""Telegram daily-digest formatter.

Produces both a structured JSON payload (consumed by n8n) and a
plain-text scannable message. EUR-denominated.
"""

from __future__ import annotations

import json
from typing import Any

from .config import ASSETS, QUOTE


def build(
    snapshot: dict,
    paper_trades: list[dict],
    history: list[dict],
) -> dict[str, Any]:
    total = sum(snapshot.get("eur_portfolio", {}).values())
    yesterday_total = sum(history[-2].get("eur_portfolio", {}).values()) if len(history) >= 2 else total
    week_ago_total = sum(history[-8].get("eur_portfolio", {}).values()) if len(history) >= 8 else total
    month_ago_total = sum(history[-31].get("eur_portfolio", {}).values()) if len(history) >= 31 else total

    def pct(now: float, prev: float) -> float:
        return ((now - prev) / prev * 100) if prev > 0 else 0.0

    decisions = [
        f"{t['side'].upper()} {t['asset']} {t['eur_amount']:.0f} EUR ({t['component']})"
        for t in paper_trades
        if t.get("approved")
    ]
    rails = sorted({rail for t in paper_trades for rail in t.get("rails_triggered", [])})

    paper_pnl_eur = snapshot.get("paper_pnl_eur", 0.0)
    bh_delta_pct = snapshot.get("buy_and_hold_delta_pct", 0.0)

    text_lines = [
        f"*Binance Shadow Cycle* — {snapshot['date']}",
        f"Portfolio: {total:.0f} EUR (d {pct(total, yesterday_total):+.2f}% | 7d {pct(total, week_ago_total):+.2f}% | 30d {pct(total, month_ago_total):+.2f}%)",
    ]
    for asset in ASSETS:
        eur = snapshot.get("eur_portfolio", {}).get(asset, 0.0)
        share = (eur / total * 100) if total else 0
        text_lines.append(f"  {asset}: {eur:.0f} EUR ({share:.1f}%)")
    if decisions:
        text_lines.append("Decisions:")
        for d in decisions:
            text_lines.append(f"  - {d}")
    else:
        text_lines.append("Decisions: hold")
    if rails:
        text_lines.append(f"Rails: {', '.join(rails)}")
    text_lines.append(f"Paper PnL: {paper_pnl_eur:+.2f} EUR | vs B&H: {bh_delta_pct:+.2f}%")

    return {
        "date": snapshot["date"],
        "total_eur": round(total, 2),
        "delta_pct": {
            "day": round(pct(total, yesterday_total), 2),
            "week": round(pct(total, week_ago_total), 2),
            "month": round(pct(total, month_ago_total), 2),
        },
        "holdings_eur": {a: round(snapshot.get("eur_portfolio", {}).get(a, 0.0), 2) for a in ASSETS},
        "decisions": decisions,
        "rails_triggered": rails,
        "paper_pnl_eur": round(paper_pnl_eur, 2),
        "buy_and_hold_delta_pct": round(bh_delta_pct, 2),
        "telegram_text": "\n".join(text_lines),
    }


def to_jsonl_line(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)

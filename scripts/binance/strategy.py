"""Hybrid shadow strategy: DCA + threshold rebalance + SMA crossover.

Deterministic — no LLM, no randomness. The same portfolio state and price
history must produce the same decisions across runs.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date

from .config import ASSETS, StrategyConfig
from .risk import RiskDecision, TradeProposal, evaluate


@dataclass
class PaperTrade:
    timestamp: str
    side: str
    asset: str
    eur_amount: float
    component: str  # "dca" | "rebalance" | "sma"
    reason: str
    rails_triggered: list[str]
    approved: bool

    def to_jsonl(self) -> str:
        import json as _json
        return _json.dumps(asdict(self))


def _sma(prices: list[float], window: int) -> float | None:
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window


def _is_first_of_month(today: date) -> bool:
    return today.day == 1


def decide(
    portfolio_eur: dict[str, float],
    prices_by_asset: dict[str, list[float]],
    daily_eur_spent: float,
    cfg: StrategyConfig,
    today: date,
) -> list[PaperTrade]:
    """Run all three components and return the resulting paper-trade list."""

    out: list[PaperTrade] = []
    ts = today.isoformat()

    if _is_first_of_month(today):
        for asset, weight in cfg.dca_weights.items():
            proposal = TradeProposal(
                side="buy",
                asset=asset,
                eur_amount=cfg.dca_monthly_eur * weight,
                reason=f"dca month-open weight={weight}",
            )
            decision = evaluate(proposal, portfolio_eur, daily_eur_spent, cfg)
            daily_eur_spent += decision.eur_amount if proposal.side == "buy" else 0
            out.append(_to_trade(ts, proposal, decision, "dca"))

    total = sum(portfolio_eur.get(a, 0.0) for a in ASSETS) or 1.0
    targets = cfg.dca_weights
    for asset in ASSETS:
        current_pct = (portfolio_eur.get(asset, 0.0) / total) * 100
        target_pct = targets[asset] * 100
        drift = current_pct - target_pct
        if abs(drift) >= cfg.rebalance_threshold_pp:
            side = "sell" if drift > 0 else "buy"
            adjust_eur = (abs(drift) / 100) * total
            proposal = TradeProposal(
                side=side,
                asset=asset,
                eur_amount=adjust_eur,
                reason=f"rebalance drift={drift:+.1f}pp (target {target_pct:.0f}%)",
            )
            decision = evaluate(proposal, portfolio_eur, daily_eur_spent, cfg)
            if side == "buy":
                daily_eur_spent += decision.eur_amount
            out.append(_to_trade(ts, proposal, decision, "rebalance"))

    for asset in ASSETS:
        prices = prices_by_asset.get(asset, [])
        short = _sma(prices, cfg.sma_short)
        long = _sma(prices, cfg.sma_long)
        if short is None or long is None:
            continue
        prev_short = _sma(prices[:-1], cfg.sma_short)
        prev_long = _sma(prices[:-1], cfg.sma_long)
        if prev_short is None or prev_long is None:
            continue

        crossed_up = prev_short <= prev_long and short > long
        crossed_down = prev_short >= prev_long and short < long
        if not (crossed_up or crossed_down):
            continue

        side = "buy" if crossed_up else "sell"
        shift_eur = min(
            (cfg.sma_max_shift_pct / 100) * total,
            (cfg.sma_max_shift_pct / 100) * portfolio_eur.get(asset, total),
        )
        proposal = TradeProposal(
            side=side,
            asset=asset,
            eur_amount=shift_eur,
            reason=(
                f"sma{cfg.sma_short}x{cfg.sma_long} cross {'up' if crossed_up else 'down'}"
            ),
        )
        decision = evaluate(proposal, portfolio_eur, daily_eur_spent, cfg)
        if side == "buy":
            daily_eur_spent += decision.eur_amount
        out.append(_to_trade(ts, proposal, decision, "sma"))

    return out


def _to_trade(ts: str, proposal: TradeProposal, decision: RiskDecision, component: str) -> PaperTrade:
    return PaperTrade(
        timestamp=ts,
        side=proposal.side,
        asset=proposal.asset,
        eur_amount=decision.eur_amount,
        component=component,
        reason=proposal.reason,
        rails_triggered=decision.rails_triggered,
        approved=decision.approved,
    )

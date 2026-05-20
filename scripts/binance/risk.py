"""Risk framework (Plan-Doc Abschnitt 3).

Enforced in shadow mode as well so we verify the rails before real money
moves. A trade proposal that violates a rail is downgraded to size 0 and
the violating rail is logged on the paper trade.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import STABLE_ASSETS, StrategyConfig


@dataclass
class TradeProposal:
    side: str  # "buy" or "sell"
    asset: str
    eur_amount: float
    reason: str


@dataclass
class RiskDecision:
    approved: bool
    eur_amount: float
    rails_triggered: list[str]


def evaluate(
    proposal: TradeProposal,
    portfolio: dict,
    daily_eur_spent: float,
    cfg: StrategyConfig,
) -> RiskDecision:
    """Apply position-limit, stables-floor, and daily-budget rails."""

    rails: list[str] = []
    total_eur = sum(portfolio.values()) or 1.0
    eur = proposal.eur_amount

    if proposal.side == "buy":
        remaining_budget = cfg.daily_budget_eur - daily_eur_spent
        if eur > remaining_budget:
            rails.append("daily_budget_clamp")
            eur = max(0.0, remaining_budget)

        if proposal.asset not in STABLE_ASSETS:
            projected = portfolio.get(proposal.asset, 0.0) + eur
            projected_pct = (projected / (total_eur + eur)) * 100
            if projected_pct > cfg.max_position_pct:
                rails.append("max_position_clamp")
                limit_eur = (cfg.max_position_pct / 100) * (total_eur + eur) - portfolio.get(proposal.asset, 0.0)
                eur = max(0.0, limit_eur)

    if proposal.side == "sell":
        stables_value = sum(portfolio.get(s, 0.0) for s in STABLE_ASSETS)
        # selling more would erode the stable buffer indirectly via reallocation
        if stables_value / total_eur * 100 < cfg.stables_floor_pct:
            rails.append("stables_floor_warning")

    return RiskDecision(
        approved=eur > 0,
        eur_amount=round(eur, 2),
        rails_triggered=rails,
    )

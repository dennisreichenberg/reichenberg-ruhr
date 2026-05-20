"""Static configuration for the Binance shadow strategy."""

from dataclasses import dataclass, field

ASSETS = ("BTC", "ETH", "BNB")
QUOTE = "EUR"
STABLE_ASSETS = ("USDT", "USDC", "EUR", "BUSD", "FDUSD")


@dataclass(frozen=True)
class StrategyConfig:
    """Defaults from REI-329 / plan-doc abschnitt 3 & 8."""

    dca_monthly_eur: float = 50.0
    dca_weights: dict = field(default_factory=lambda: {"BTC": 0.60, "ETH": 0.30, "BNB": 0.10})
    rebalance_threshold_pp: float = 5.0
    sma_short: int = 50
    sma_long: int = 200
    sma_max_shift_pct: float = 10.0
    stables_floor_pct: float = 10.0
    daily_budget_eur: float = 100.0
    max_position_pct: float = 70.0


def load() -> StrategyConfig:
    return StrategyConfig()

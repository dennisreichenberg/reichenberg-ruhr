"""Binance API client wrapper.

Order endpoints are hard-disabled. Read-only endpoints are pulled via
python-binance when a real key is present, otherwise we fall back to
fixtures so the rest of the pipeline can be exercised without an account.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import PHASE


class PhaseError(RuntimeError):
    """Raised when code attempts a write operation in a non-trading phase."""


@dataclass
class Credentials:
    api_key: str
    api_secret: str
    testnet: bool = False

    @classmethod
    def from_file(cls, path: Path) -> "Credentials":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            api_key=data["api_key"],
            api_secret=data["api_secret"],
            testnet=bool(data.get("testnet", False)),
        )


class BinanceClient:
    """Wrapper around python-binance with order endpoints permanently disabled.

    Read methods accept a `fixtures_dir` argument; when set, no network
    call is made and fixtures are returned instead. This keeps the rest
    of the pipeline testable before a real key is provisioned.
    """

    def __init__(
        self,
        credentials: Credentials | None = None,
        fixtures_dir: Path | None = None,
    ):
        self._creds = credentials
        self._fixtures_dir = fixtures_dir
        self._client = None
        if credentials is not None and fixtures_dir is None:
            try:
                from binance.client import Client  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "python-binance is required for live mode; "
                    "pip install -r scripts/binance/requirements.txt"
                ) from exc
            self._client = Client(
                credentials.api_key,
                credentials.api_secret,
                testnet=credentials.testnet,
            )

    def _fixture(self, name: str) -> Any:
        assert self._fixtures_dir is not None
        return json.loads((self._fixtures_dir / name).read_text(encoding="utf-8"))

    def get_account(self) -> dict:
        if self._fixtures_dir is not None:
            return self._fixture("account.json")
        return self._client.get_account()  # type: ignore[union-attr]

    def get_my_trades(self, symbol: str, limit: int = 100) -> list[dict]:
        if self._fixtures_dir is not None:
            data = self._fixture("my_trades.json")
            return [t for t in data if t["symbol"] == symbol][:limit]
        return self._client.get_my_trades(symbol=symbol, limit=limit)  # type: ignore[union-attr]

    def get_klines(self, symbol: str, interval: str = "1d", limit: int = 365) -> list[list]:
        if self._fixtures_dir is not None:
            data = self._fixture("klines.json")
            return data.get(symbol, [])[:limit]
        return self._client.get_klines(symbol=symbol, interval=interval, limit=limit)  # type: ignore[union-attr]

    def get_symbol_ticker(self, symbol: str) -> dict:
        if self._fixtures_dir is not None:
            tickers = self._fixture("tickers.json")
            return {"symbol": symbol, "price": tickers[symbol]}
        return self._client.get_symbol_ticker(symbol=symbol)  # type: ignore[union-attr]

    def place_order(self, *_args, **_kwargs):
        """Hard-disabled in Phase 1. Calling this raises immediately.

        Reactivation requires (a) PHASE flip to "live" AND (b) explicit
        removal of this guard AND (c) a fresh Dennis-approval via Telegram.
        Do not silence this without REI-329 phase-2 sign-off.
        """
        raise PhaseError(
            f"place_order() is disabled in PHASE={PHASE!r}. "
            "Phase 2 requires Dennis-approval via Telegram (REI-205)."
        )

    def withdraw(self, *_args, **_kwargs):
        """Permanently disabled. The agent never moves funds off-exchange."""
        raise PhaseError("withdraw() is permanently disabled for this agent.")

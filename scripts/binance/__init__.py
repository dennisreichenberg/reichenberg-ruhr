"""Binance trading agent (read-only Phase 1).

Phase 1 contract:
- Read-only API usage (account, myTrades, klines).
- Order endpoints are hard-disabled; calling place_order() raises immediately.
- Withdraw endpoints are never implemented.
- All trades are paper trades in data/treasury/paper_trades.jsonl.

Phase transitions require explicit Dennis approval via Telegram (REI-205).
"""

PHASE = "read_only"
"""Top-level phase guard. Mutating to anything else without removing the
hard-disable guard in client.place_order() does NOT enable trading."""

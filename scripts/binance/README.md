# Binance Trading Agent — Phase 1 (read-only shadow)

## Was das ist

Phase 1 des Binance-Trading-Agents (REI-329). Liest Portfolio + Klines von Binance, laesst eine deterministische Hybrid-Strategie (DCA + Threshold-Rebalance + SMA-Crossover) im Schatten laufen und schickt eine taegliche Zusammenfassung via Telegram. **Es werden keine echten Trades ausgeloest.**

## Hard-Gates

- `PHASE = "read_only"` in `scripts/binance/__init__.py`.
- `BinanceClient.place_order()` und `BinanceClient.withdraw()` werfen sofort `PhaseError`. Ein Flag-Flip allein reicht nicht, die Guards sind doppelt gesichert (Phase-Constant + Method-Body).
- Phase-2-Aktivierung verlangt: (a) Dennis-Approval via Telegram (REI-205), (b) explizites Entfernen der Method-Guards mit Review.

## Verwendung

### Mit Fixtures (vor Real-Key)

```bash
pip install -r scripts/binance/requirements.txt   # nur fuer Live-Mode noetig
python -m scripts.binance.cycle --fixtures scripts/binance/fixtures --print-digest
```

Schreibt:
- `data/treasury/snapshot-YYYYMMDD.json` (Portfolio + Preise + Quantities)
- `data/treasury/paper_trades.jsonl` (Strategie-Entscheidungen, append-only)
- `data/treasury/digest-YYYYMMDD.json` (Telegram-Payload)

### Mit Real-Key (nach REI-329-Gate)

`secrets/binance.json` anlegen (NICHT eingecheckt):

```json
{
  "api_key": "...",
  "api_secret": "...",
  "testnet": false
}
```

Dann:

```bash
python -m scripts.binance.cycle --print-digest
```

### Testnet

Setze `"testnet": true` in `secrets/binance.json`. Keys werden auf https://testnet.binance.vision/ erstellt.

## Tests

```bash
python -m scripts.binance.tests.smoke
```

Smoke-Test pruef Strategie-Determinismus, Risk-Rails, Order-Guard.

## Strategie-Komponenten

1. **DCA** (Monatsanfang): 50 EUR verteilt auf 60% BTC / 30% ETH / 10% BNB.
2. **Threshold-Rebalance**: wenn ein Asset > 5pp vom Target-Anteil abweicht, simuliere Adjust-Trade.
3. **SMA-Crossover** (50d × 200d): bei Cross-Up/Down maximal 10% Portfolio-Verschiebung im Schatten.

Default-Werte in `config.py`. Risk-Rails (Daily-Budget, Position-Limit, Stables-Floor) werden auch im Schatten enforced.

## Open Questions vor Phase 2

- Default-DCA-Splits (60/30/10) finalisiert mit Dennis?
- Daily-Budget-Cap (aktuell 100 EUR) korrekt fuer Dennis' Account-Size?
- Wochen-Report-Zeitpunkt: Sonntag 20:00 Berlin OK?

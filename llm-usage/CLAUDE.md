# CLAUDE.md - llm-usage/

ASCII-only. Use `->` not the Unicode arrow, `--` not an em-dash, straight
quotes. The repo enforces a CP1252 constraint, so do not introduce characters
outside that codepage.

## Zweck

`llm-usage` ist die historische Nutzungs- und Kostenbuchhaltung fuer Dennis'
KI-Infrastruktur. Es konsumiert die Request-Logs, die `litellm-proxy`
(`llm-gateway`) ohnehin schreibt, persistiert pro Request eine Zeile
(Zeitstempel, Modell, Backend, Prompt-/Completion-Tokens, Latenz, geschaetzte
Cloud-$) und aggregiert sie ueber beliebige Zeitraeume.

Es ist KEIN Proxy. Es startet keinen Server und faengt keinen Traffic ab -- es
liest vorhandene Logdaten. Wenn ein Logging-Hook fehlt, gehoert der in
`litellm-proxy`, nicht hierher.

## Abgrenzung (kein Doppel bauen)

- `vllm-monitor` -> Echtzeit-Metrik (kein Verlauf).
- `litellm-proxy` / `llm-gateway` -> routet, fuehrt kein Nutzungsregister.
- `llm-bench` -> synthetisches Benchmarking.
- `prompt-eval` / `model-eval` -> Qualitaets-Evals.
- `llm-usage` -> dauerhafte Nutzungs-/Kostenbuchhaltung.

## Architektur

```
litellm-proxy logs (JSONL)        pricing.yaml (USD / 1M tokens)
        |                                |
        v                                v
   ingest.py  -- normalize -->  UsageRecord  -- estimate cost
        |
        v
     db.py (SQLite: requests table)
        |
        v
   cli.py: report / top / export
```

## Dateien

| Datei                        | Was drin steht                                         |
|------------------------------|--------------------------------------------------------|
| `src/llm_usage/models.py`    | `UsageRecord` dataclass (das normalisierte Schema)     |
| `src/llm_usage/ingest.py`    | JSONL-Parser (LiteLLM + generisch), tolerante Feldsuche|
| `src/llm_usage/pricing.py`   | YAML-Preis-Tabelle -> Kostenschaetzung                 |
| `src/llm_usage/pricing.yaml` | Default-Preise (USD pro 1.000.000 Tokens)              |
| `src/llm_usage/db.py`        | SQLite-Store + Aggregations-Queries                    |
| `src/llm_usage/cli.py`       | Click-CLI: ingest / report / top / export              |
| `examples/`                  | Beispiel-Log zum Ausprobieren ohne echte Daten         |
| `tests/`                     | pytest (pricing, ingest, db, cli end-to-end)           |

## Befehle

- `llm-usage ingest LOGFILE... [--db] [--pricing] [--stdin]`
- `llm-usage report [--by model|backend|day] [--since] [--until] [--json]`
- `llm-usage top [--metric cost|tokens|requests] [--by model|backend] [--limit] [--json]`
- `llm-usage export [--format json|csv] [--since] [--until] [-o FILE]`

## Konventionen

- src-Layout + hatchling, identisch zu `ollama-monitor/`.
- Nur zwei Laufzeit-Deps: `click`, `PyYAML`. SQLite ist stdlib. Keine weiteren
  Deps ohne guten Grund.
- Zeitstempel werden als ISO8601-UTC-String `YYYY-MM-DDTHH:MM:SSZ` gespeichert,
  damit lexikografischer Vergleich == chronologischer Vergleich ist.
- Ingestion ist idempotent: Dedup ueber `request_id`. Erneutes Einlesen
  ueberlappender Logs zaehlt nicht doppelt.
- Kosten werden beim Ingest berechnet und gespeichert, damit Reports billig
  bleiben. Re-Ingest mit anderer `--pricing` schaetzt neu (nur fuer neue Zeilen;
  bestehende request_ids werden uebersprungen).

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Wahrscheinliche Folge-Aufgaben

- Weitere Log-Quellen (z.B. natives Ollama Access-Log) als zusaetzliche
  Parser-Shape in `ingest.py`.
- `report --by model,day` (mehrdimensional) falls gebraucht.
- Optionaler Langfuse-Import als Alternative zu Datei-Logs.

## Verwandte Tickets

- REI-418 -- dieses Tool.
- REI-408 -- Tool-Gap-Analyse (Parent).
- REI-266 -- litellm-proxy (Log-Quelle).
- REI-419 -- Profil-Repo + README-Discoverability verifizieren.

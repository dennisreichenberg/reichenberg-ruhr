# llm-usage

Historical request and cost accounting across all LLM backends -- local
(Ollama / vLLM) and cloud. It consumes the request logs that
`llm-gateway` / `litellm-proxy` already produce, persists one row per request
(timestamp, model, backend, prompt/completion tokens, latency, estimated cloud
cost), and reports aggregates over any time range.

This fills the gap that the neighbouring tools leave open:

- `vllm-monitor` -> real-time metrics only (no history).
- `llm-gateway` / `litellm-proxy` -> routes requests, keeps no usage ledger.
- `llm-bench` -> synthetic benchmarking.
- `prompt-eval` / `model-eval` -> output quality, not usage/cost.

`llm-usage` is the durable usage-and-cost ledger.

## Install

```bash
pip install -e .
```

This puts an `llm-usage` command on your PATH (Python 3.11+).

## Quickstart

```bash
# 1. Ingest request logs (LiteLLM JSONL, or the generic flat shape).
llm-usage ingest examples/sample-litellm.jsonl

# 2. Aggregate.
llm-usage report                 # by model (default)
llm-usage report --by backend
llm-usage report --by day --since 2026-05-20 --until 2026-05-22

# 3. Biggest consumers.
llm-usage top --metric cost --limit 5
llm-usage top --metric tokens --by backend

# 4. Export the raw ledger.
llm-usage export --format json -o usage.json
llm-usage export --format csv  -o usage.csv
```

Example `report` output:

```
model              requests  prompt  completion  total  avg_ms  cost_usd  errors
-----------------  --------  ------  ----------  -----  ------  --------  ------
gpt-4o             3         4200    2040        6040   2350    0.0298    1
claude-3-5-sonnet  1         2200    880         3080   2250    0.0198    0
...
TOTAL              10        ...                                0.0xxx    1
```

## Input format

Newline-delimited JSON (JSONL), one request per line. Two shapes are understood
and may be mixed in one file:

1. **LiteLLM standard logging payload** (what `litellm-proxy` emits with
   `json_logs: true`): keys such as `start_time`, `end_time`, `model`,
   `custom_llm_provider`, `response_cost`, and a nested `usage` object.
2. **Generic flat shape**: `timestamp`, `model`, `backend`, `prompt_tokens`,
   `completion_tokens`, `latency_ms`.

Field lookup is tolerant -- each logical field is read from the first matching
key, so minor format drift does not break ingestion. Lines that are blank, not
JSON, or carry no model are skipped and counted.

You can also pipe logs in:

```bash
docker logs litellm-proxy 2>&1 | grep '^{' | llm-usage ingest --stdin
```

### Wiring up litellm-proxy

`litellm-proxy/litellm_config.yaml` already sets `json_logs: true`. Capture the
container's stdout to a file and point `llm-usage ingest` at it, e.g. via a cron
that appends `docker logs --since 24h litellm` to a rotating JSONL file. No proxy
changes are required; `llm-usage` is a pure consumer.

## Cost estimation

Cloud cost is estimated from a configurable YAML price table
(`src/llm_usage/pricing.yaml`, USD per 1,000,000 tokens). If a log line already
carries a `response_cost`, that authoritative value is used as-is; otherwise the
cost is estimated. Local backends (`ollama`, `vllm`) resolve to `0`.

Override the table per run:

```bash
llm-usage ingest mylogs.jsonl --pricing my-prices.yaml
```

Resolution order: exact model -> model with provider prefix stripped ->
backend default -> global default.

## Storage

SQLite (stdlib `sqlite3`). Default location is `~/.llm-usage/usage.db`, override
with `--db PATH` or the `LLM_USAGE_DB` env var. Ingestion is idempotent: rows
are de-duplicated by request id, so re-running `ingest` on overlapping logs does
not double-count.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## License

MIT

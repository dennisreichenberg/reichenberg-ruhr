# llm-cache

Semantic response cache that sits in front of an OpenAI-compatible LLM gateway
(`ollama-proxy`, `litellm`, or any local Ollama/vLLM exposing the OpenAI API).
Identical or semantically similar prompts return cached responses instead of
re-running inference -- saving tokens and latency without changing your client
code.

## Features

- OpenAI-compatible HTTP proxy: `/v1/chat/completions` + `/v1/embeddings`
- Exact-match cache keyed on `(model, messages, temperature, top_p, max_tokens, stop, seed)`
- Optional semantic mode: embed the last user message and hit on cosine >= 0.97
- SQLite backend (default) with TTL + LRU eviction; Redis backend planned via extras
- Per-request bypass via `X-LLM-Cache: bypass` and forced rewrite via `X-LLM-Cache: refresh`
- Streaming requests (`stream: true`) are bypassed in MVP, not cached
- Structured JSONL logging at `~/.llm-cache/log.jsonl`
- Runtime metrics on `GET /stats` (hit/miss counts, bytes saved, tokens-saved estimate)

## Install

```bash
pip install -e .
# with semantic-mode embedder
pip install -e ".[semantic]"
# dev extras (pytest, ruff)
pip install -e ".[dev]"
```

## Usage

### Start the proxy

```bash
# default: listen on 127.0.0.1:4118, forward to http://localhost:4117 (ollama-proxy)
llm-cache serve

# point at a vanilla Ollama OpenAI endpoint
llm-cache serve --upstream http://localhost:11434

# enable semantic-mode caching (requires sentence-transformers)
llm-cache serve --semantic --threshold 0.97
```

### Routing

```
client --> llm-cache (127.0.0.1:4118)  --> ollama-proxy (127.0.0.1:4117) --> Ollama / vLLM
```

Any OpenAI client (`openai`, `curl`, `litellm` SDK, ...) can point its
`base_url` at `http://127.0.0.1:4118/v1` and the cache becomes transparent.

### Example

```bash
curl http://127.0.0.1:4118/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "temperature": 0.0
  }'
```

Inspect headers on the response:
- `X-LLM-Cache-Status: miss`        first call
- `X-LLM-Cache-Status: hit-exact`   second call, identical request
- `X-LLM-Cache-Status: hit-semantic` semantic match within threshold
- `X-LLM-Cache-Status: bypass`      bypass header set
- `X-LLM-Cache-Status: refresh`     refresh header set

Force a fresh inference for one request:

```bash
curl -H "X-LLM-Cache: bypass" -H "Content-Type: application/json" \
     -d '{ "model": "llama3", "messages": [...] }' \
     http://127.0.0.1:4118/v1/chat/completions
```

### CLI

```bash
llm-cache serve                       # start the proxy
llm-cache stats                       # show local cache size/entries
llm-cache stats --json
llm-cache purge --expired-only        # drop expired entries
llm-cache purge --yes                 # drop everything
llm-cache export                      # dump entries as JSON to stdout
llm-cache export --out cache.json
```

The running server also exposes:
- `GET  /healthz` -- liveness probe
- `GET  /stats`   -- live hit/miss metrics + store stats
- `POST /admin/purge` -- drop all entries

### Config

`~/.llm-cache/config.yaml` (optional):

```yaml
upstream: http://localhost:4117
db_path: ~/.llm-cache/cache.sqlite3
ttl_seconds: 604800       # 7 days
max_entries: 10000
semantic: false
threshold: 0.97
embedding_model: sentence-transformers/all-MiniLM-L6-v2
host: 127.0.0.1
port: 4118
```

Environment variables override the file: `LLM_CACHE_UPSTREAM`, `LLM_CACHE_TTL_SECONDS`,
`LLM_CACHE_SEMANTIC`, `LLM_CACHE_THRESHOLD`, `LLM_CACHE_PORT`, ...

## Conventions

- ASCII-only in source code and comments (umlauts written as ae/oe/ue/ss).
- No external cloud calls. Embedding model runs locally via sentence-transformers
  if available; otherwise a deterministic bag-of-words stub keeps the plumbing
  testable.

## Out of Scope (MVP)

- Multi-user authentication
- Cluster mode / replicated cache
- Streaming-response caching (streaming requests are bypassed)

## Development

```bash
pip install -e ".[dev]"
pytest -v
ruff check src/ tests/
```

## License

MIT

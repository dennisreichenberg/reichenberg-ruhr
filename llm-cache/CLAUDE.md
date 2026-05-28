# llm-cache

Semantic response cache that fronts an OpenAI-compatible LLM gateway
(`ollama-proxy`, `litellm`, vanilla Ollama).

## Stack

- Python 3.11+
- FastAPI + uvicorn (async OpenAI-compatible proxy)
- httpx (async upstream forwarder, also used by tests via MockTransport)
- SQLite (default cache backend, WAL mode)
- sentence-transformers (optional, for semantic-mode embeddings)
- click (CLI)

## Project structure

```
llm-cache/
  pyproject.toml
  README.md
  LICENSE
  src/llm_cache/
    __init__.py
    __main__.py        # python -m llm_cache entry
    cli.py             # click CLI: serve / stats / purge / export
    config.py          # Config dataclass, yaml + env overlay
    proxy.py           # FastAPI app factory: /v1/chat/completions, /v1/embeddings
    store.py           # CacheStore (SQLite), cosine similarity
    keys.py            # cache-key hashing, last-user-message extraction
    semantic.py        # SentenceTransformer + StubEmbedder fallback
    metrics.py         # in-process metrics counters
    logging.py         # structured JSONL logger
  tests/
    test_keys.py
    test_store.py
    test_metrics.py
    test_config.py
    test_proxy.py      # uses httpx MockTransport for upstream
    test_cli.py
```

## Commands

```bash
pip install -e ".[dev]"
pytest -v
ruff check src/ tests/

# run the proxy
llm-cache serve --upstream http://localhost:4117
# or
python -m llm_cache serve
```

## Cache semantics

- Exact key: SHA256 of canonical-JSON of `(model, messages, temperature, top_p,
  max_tokens, stop, seed)`.
- Semantic key: per-model bucket, cosine >= threshold against the embedding of
  the last user message. Only consulted on exact-match miss when
  `cfg.semantic=True`.
- Bypass header `X-LLM-Cache: bypass` skips read AND write.
- Refresh header `X-LLM-Cache: refresh` skips read, forces write.
- Streaming (`stream: true`) is always bypassed in the MVP.
- TTL default 7 days, LRU eviction when entries > max_entries.

## Encoding

ASCII-only in source/tests (`ae/oe/ue/ss` for umlauts, no Unicode arrows,
no em-dashes).

"""End-to-end proxy tests using a fake upstream via httpx MockTransport.

Covers acceptance criterion 6 ("send same prompt twice, second is a hit") in
unit-test form without needing a real ollama-proxy on :4117.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from llm_cache.config import Config
from llm_cache.proxy import create_app
from llm_cache.store import CacheStore


def _make_upstream(counter: dict[str, int]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        counter["calls"] = counter.get("calls", 0) + 1
        if request.url.path == "/v1/chat/completions":
            body = json.dumps(
                {
                    "id": f"chatcmpl-{counter['calls']}",
                    "object": "chat.completion",
                    "model": "llama3",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "hi there"},
                            "finish_reason": "stop",
                        }
                    ],
                }
            ).encode()
            return httpx.Response(200, content=body, headers={"content-type": "application/json"})
        if request.url.path == "/v1/embeddings":
            body = json.dumps(
                {
                    "object": "list",
                    "data": [{"object": "embedding", "embedding": [0.1, 0.2, 0.3], "index": 0}],
                    "model": "nomic-embed",
                }
            ).encode()
            return httpx.Response(200, content=body, headers={"content-type": "application/json"})
        return httpx.Response(404, content=b"not found")

    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


def _make_cfg(tmp_path: Path) -> Config:
    return replace(
        Config(),
        db_path=tmp_path / "cache.sqlite",
        log_path=tmp_path / "log.jsonl",
        upstream="http://fake-upstream",
        request_timeout=5.0,
    )


def test_chat_completions_hit_on_second_call(tmp_path: Path) -> None:
    counter: dict[str, int] = {}
    upstream = _make_upstream(counter)
    cfg = _make_cfg(tmp_path)
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    app = create_app(cfg=cfg, store=store, http_client=upstream)

    with TestClient(app) as client:
        payload = {
            "model": "llama3",
            "messages": [{"role": "user", "content": "say hi"}],
            "temperature": 0.0,
        }
        r1 = client.post("/v1/chat/completions", json=payload)
        assert r1.status_code == 200
        assert r1.headers["X-LLM-Cache-Status"] == "miss"
        first_body = r1.json()

        r2 = client.post("/v1/chat/completions", json=payload)
        assert r2.status_code == 200
        assert r2.headers["X-LLM-Cache-Status"] == "hit-exact"
        # Same response bytes from the cache
        assert r2.json() == first_body

    assert counter["calls"] == 1


def test_chat_completions_bypass_header(tmp_path: Path) -> None:
    counter: dict[str, int] = {}
    upstream = _make_upstream(counter)
    cfg = _make_cfg(tmp_path)
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    app = create_app(cfg=cfg, store=store, http_client=upstream)

    with TestClient(app) as client:
        payload = {
            "model": "llama3",
            "messages": [{"role": "user", "content": "hello"}],
        }
        # First call seeds the cache.
        client.post("/v1/chat/completions", json=payload)
        assert counter["calls"] == 1

        # bypass: must hit upstream and NOT use cache.
        r = client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"X-LLM-Cache": "bypass"},
        )
        assert r.status_code == 200
        assert r.headers["X-LLM-Cache-Status"] == "bypass"
        assert counter["calls"] == 2

        # bypass must not have overwritten cache.
        r3 = client.post("/v1/chat/completions", json=payload)
        assert r3.headers["X-LLM-Cache-Status"] == "hit-exact"
        assert counter["calls"] == 2


def test_chat_completions_refresh_header(tmp_path: Path) -> None:
    counter: dict[str, int] = {}
    upstream = _make_upstream(counter)
    cfg = _make_cfg(tmp_path)
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    app = create_app(cfg=cfg, store=store, http_client=upstream)

    with TestClient(app) as client:
        payload = {
            "model": "llama3",
            "messages": [{"role": "user", "content": "hi"}],
        }
        client.post("/v1/chat/completions", json=payload)
        assert counter["calls"] == 1

        r = client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"X-LLM-Cache": "refresh"},
        )
        assert r.headers["X-LLM-Cache-Status"] == "refresh"
        assert counter["calls"] == 2
        first_body_after_refresh = r.json()

        # The cache should have been overwritten with the new response.
        r3 = client.post("/v1/chat/completions", json=payload)
        assert r3.headers["X-LLM-Cache-Status"] == "hit-exact"
        assert r3.json() == first_body_after_refresh


def test_streaming_is_bypassed(tmp_path: Path) -> None:
    counter: dict[str, int] = {}
    upstream = _make_upstream(counter)
    cfg = _make_cfg(tmp_path)
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    app = create_app(cfg=cfg, store=store, http_client=upstream)

    with TestClient(app) as client:
        payload = {
            "model": "llama3",
            "messages": [{"role": "user", "content": "x"}],
            "stream": True,
        }
        r1 = client.post("/v1/chat/completions", json=payload)
        r2 = client.post("/v1/chat/completions", json=payload)
        assert r1.headers["X-LLM-Cache-Status"] == "bypass-stream"
        assert r2.headers["X-LLM-Cache-Status"] == "bypass-stream"
        assert counter["calls"] == 2


def test_embeddings_hit(tmp_path: Path) -> None:
    counter: dict[str, int] = {}
    upstream = _make_upstream(counter)
    cfg = _make_cfg(tmp_path)
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    app = create_app(cfg=cfg, store=store, http_client=upstream)

    with TestClient(app) as client:
        payload = {"model": "nomic-embed", "input": "hello world"}
        r1 = client.post("/v1/embeddings", json=payload)
        r2 = client.post("/v1/embeddings", json=payload)
        assert r1.headers["X-LLM-Cache-Status"] == "miss"
        assert r2.headers["X-LLM-Cache-Status"] == "hit-exact"
        assert counter["calls"] == 1


def test_semantic_hit_with_stub_embedder(tmp_path: Path) -> None:
    """Force semantic mode + stub embedder; near-identical prompts should hit."""
    from llm_cache.semantic import StubEmbedder

    counter: dict[str, int] = {}
    upstream = _make_upstream(counter)
    cfg = replace(_make_cfg(tmp_path), semantic=True, threshold=0.9)
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    app = create_app(
        cfg=cfg, store=store, http_client=upstream, embedder=StubEmbedder()
    )

    with TestClient(app) as client:
        payload_a = {
            "model": "llama3",
            "messages": [{"role": "user", "content": "hello world how are you"}],
        }
        r1 = client.post("/v1/chat/completions", json=payload_a)
        assert r1.headers["X-LLM-Cache-Status"] == "miss"
        # Same words, slightly reordered - exact-match miss but semantic hit.
        payload_b = {
            "model": "llama3",
            "messages": [{"role": "user", "content": "how are you hello world"}],
        }
        r2 = client.post("/v1/chat/completions", json=payload_b)
        # With the bag-of-words stub embedder these are identical vectors,
        # so we either hit exact (unlikely - different message text) or semantic.
        assert r2.headers["X-LLM-Cache-Status"] in {"hit-semantic", "hit-exact"}
        assert counter["calls"] == 1


def test_stats_and_purge_endpoints(tmp_path: Path) -> None:
    counter: dict[str, int] = {}
    upstream = _make_upstream(counter)
    cfg = _make_cfg(tmp_path)
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    app = create_app(cfg=cfg, store=store, http_client=upstream)

    with TestClient(app) as client:
        payload = {"model": "llama3", "messages": [{"role": "user", "content": "x"}]}
        client.post("/v1/chat/completions", json=payload)
        client.post("/v1/chat/completions", json=payload)
        stats = client.get("/stats").json()
        assert stats["metrics"]["hits_exact"] == 1
        assert stats["metrics"]["misses"] == 1
        assert stats["store"]["entries"] == 1

        purge = client.post("/admin/purge").json()
        assert purge["removed"] == 1
        assert client.get("/stats").json()["store"]["entries"] == 0


def test_upstream_error_returns_502(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    upstream = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    cfg = _make_cfg(tmp_path)
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    app = create_app(cfg=cfg, store=store, http_client=upstream)

    with TestClient(app) as client:
        r = client.post(
            "/v1/chat/completions",
            json={"model": "x", "messages": [{"role": "user", "content": "y"}]},
        )
        assert r.status_code == 502
        assert r.headers["X-LLM-Cache-Status"] == "upstream-error"

"""FastAPI-based OpenAI-compatible caching proxy.

Routes:
  POST /v1/chat/completions   - cached (exact + optional semantic)
  POST /v1/embeddings         - cached (exact)
  GET  /healthz               - liveness
  GET  /stats                 - JSON metrics + store stats
  POST /admin/purge           - purge all entries

Bypass headers:
  X-LLM-Cache: bypass   -> skip lookup, forward upstream, do not store
  X-LLM-Cache: refresh  -> skip lookup, forward upstream, overwrite cache
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from llm_cache.config import Config, ensure_data_dir
from llm_cache.keys import chat_key, embedding_key, last_user_message, semantic_bucket
from llm_cache.logging import JsonlLogger
from llm_cache.metrics import MetricsRegistry
from llm_cache.semantic import load_embedder
from llm_cache.store import CacheStore

CACHE_HEADER = "x-llm-cache"
CACHE_STATUS_HEADER = "X-LLM-Cache-Status"


def _is_streaming(body: dict[str, Any]) -> bool:
    return bool(body.get("stream", False))


def _decode_json(raw: bytes) -> Optional[dict[str, Any]]:
    if not raw:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def create_app(
    cfg: Optional[Config] = None,
    store: Optional[CacheStore] = None,
    http_client: Optional[httpx.AsyncClient] = None,
    embedder: Optional[Any] = None,
) -> FastAPI:
    cfg = cfg or Config()
    ensure_data_dir(cfg)

    store = store or CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    metrics = MetricsRegistry()
    logger = JsonlLogger(cfg.log_path)

    if cfg.semantic and embedder is None:
        embedder = load_embedder(cfg.embedding_model)
    if cfg.semantic and embedder is None:
        logger.emit("embedder_unavailable", model=cfg.embedding_model)

    owned_client = http_client is None
    client = http_client or httpx.AsyncClient(timeout=cfg.request_timeout)

    app = FastAPI(title="llm-cache", version="0.1.0")
    app.state.store = store
    app.state.metrics = metrics
    app.state.config = cfg
    app.state.logger = logger
    app.state.embedder = embedder

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # pragma: no cover - lifecycle glue
        if owned_client:
            await client.aclose()
        store.close()

    # --------------------------------------------------------------- routes

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {"ok": True, "upstream": cfg.upstream}

    @app.get("/stats")
    async def stats() -> dict[str, Any]:
        return {"metrics": metrics.snapshot(), "store": store.stats()}

    @app.post("/admin/purge")
    async def admin_purge() -> dict[str, Any]:
        removed = store.purge_all()
        logger.emit("purge_all", removed=removed)
        return {"removed": removed}

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request) -> Response:
        raw = await request.body()
        payload = _decode_json(raw)
        if payload is None:
            return _proxy_passthrough(
                "POST", "/v1/chat/completions", raw, request, kind="chat", reason="bad_json"
            )

        mode = (request.headers.get(CACHE_HEADER) or "").strip().lower()

        if _is_streaming(payload):
            # MVP: streaming is bypassed (the spec explicitly allows this).
            metrics.bypass()
            logger.emit("bypass_streaming", model=payload.get("model"))
            return await _forward(
                request,
                "/v1/chat/completions",
                raw,
                upstream_kind="chat",
                store_response=False,
                payload=payload,
                cache_status="bypass-stream",
            )

        if mode == "bypass":
            metrics.bypass()
            logger.emit("bypass_header", model=payload.get("model"))
            return await _forward(
                request,
                "/v1/chat/completions",
                raw,
                upstream_kind="chat",
                store_response=False,
                payload=payload,
                cache_status="bypass",
            )

        ek = chat_key(payload)

        if mode != "refresh":
            hit = store.get(ek)
            if hit is not None:
                metrics.hit_exact(len(hit.body))
                logger.emit(
                    "hit_exact",
                    model=payload.get("model"),
                    key=ek,
                    bytes=len(hit.body),
                )
                return Response(
                    content=hit.body,
                    media_type=hit.content_type or "application/json",
                    headers={CACHE_STATUS_HEADER: "hit-exact"},
                )

            # Semantic-mode lookup.
            if cfg.semantic and embedder is not None:
                prompt = last_user_message(payload)
                if prompt:
                    try:
                        query_vec = embedder.encode(prompt)
                    except Exception as exc:  # pragma: no cover - embedder defensive
                        logger.emit("embed_error", error=str(exc))
                        query_vec = None
                    if query_vec is not None:
                        bucket = semantic_bucket(str(payload.get("model", "")))
                        match = store.semantic_lookup(bucket, query_vec, cfg.threshold)
                        if match is not None:
                            entry, sim = match
                            metrics.hit_semantic(len(entry.body))
                            logger.emit(
                                "hit_semantic",
                                model=payload.get("model"),
                                similarity=sim,
                                bytes=len(entry.body),
                            )
                            return Response(
                                content=entry.body,
                                media_type=entry.content_type or "application/json",
                                headers={
                                    CACHE_STATUS_HEADER: "hit-semantic",
                                    "X-LLM-Cache-Similarity": f"{sim:.4f}",
                                },
                            )
        # Miss / refresh: forward to upstream and (re)store.
        if mode == "refresh":
            metrics.refresh()
            cache_status = "refresh"
        else:
            metrics.miss()
            cache_status = "miss"
        return await _forward(
            request,
            "/v1/chat/completions",
            raw,
            upstream_kind="chat",
            store_response=True,
            payload=payload,
            cache_key=ek,
            cache_status=cache_status,
        )

    @app.post("/v1/embeddings")
    async def embeddings(request: Request) -> Response:
        raw = await request.body()
        payload = _decode_json(raw)
        if payload is None:
            return _proxy_passthrough(
                "POST", "/v1/embeddings", raw, request, kind="embedding", reason="bad_json"
            )

        mode = (request.headers.get(CACHE_HEADER) or "").strip().lower()

        if mode == "bypass":
            metrics.bypass()
            return await _forward(
                request,
                "/v1/embeddings",
                raw,
                upstream_kind="embedding",
                store_response=False,
                payload=payload,
                cache_status="bypass",
            )

        ek = embedding_key(payload)
        if mode != "refresh":
            hit = store.get(ek)
            if hit is not None:
                metrics.hit_exact(len(hit.body))
                logger.emit("hit_exact_embedding", model=payload.get("model"), key=ek)
                return Response(
                    content=hit.body,
                    media_type=hit.content_type or "application/json",
                    headers={CACHE_STATUS_HEADER: "hit-exact"},
                )

        if mode == "refresh":
            metrics.refresh()
        else:
            metrics.miss()
        return await _forward(
            request,
            "/v1/embeddings",
            raw,
            upstream_kind="embedding",
            store_response=True,
            payload=payload,
            cache_key=ek,
            cache_status="refresh" if mode == "refresh" else "miss",
        )

    # --------------------------------------------------------------- helpers

    async def _forward(
        request: Request,
        path: str,
        body: bytes,
        *,
        upstream_kind: str,
        store_response: bool,
        payload: dict[str, Any],
        cache_key: Optional[str] = None,
        cache_status: str = "miss",
    ) -> Response:
        url = cfg.upstream.rstrip("/") + path
        forward_headers = _strip_hop_headers(dict(request.headers))
        forward_headers.pop("host", None)
        forward_headers.pop("content-length", None)
        try:
            upstream_resp = await client.post(url, content=body, headers=forward_headers)
        except httpx.HTTPError as exc:
            metrics.upstream_error()
            logger.emit("upstream_error", path=path, error=str(exc))
            return JSONResponse(
                status_code=502,
                content={"error": {"type": "upstream_unavailable", "message": str(exc)}},
                headers={CACHE_STATUS_HEADER: "upstream-error"},
            )

        resp_headers = {
            k: v
            for k, v in upstream_resp.headers.items()
            if k.lower() not in {"content-length", "transfer-encoding", "connection"}
        }
        resp_headers[CACHE_STATUS_HEADER] = cache_status

        body_out = upstream_resp.content
        content_type = upstream_resp.headers.get("content-type", "application/json")

        if store_response and upstream_resp.status_code == 200 and cache_key is not None:
            prompt = None
            embedding_vec = None
            if upstream_kind == "chat" and cfg.semantic and embedder is not None:
                prompt = last_user_message(payload)
                if prompt:
                    try:
                        embedding_vec = embedder.encode(prompt)
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.emit("embed_error_store", error=str(exc))
                        embedding_vec = None
            bucket = (
                semantic_bucket(str(payload.get("model", "")))
                if upstream_kind == "chat"
                else "embedding"
            )
            try:
                store.put(
                    key=cache_key,
                    bucket=bucket,
                    body=body_out,
                    content_type=content_type,
                    prompt=prompt,
                    embedding=embedding_vec,
                )
            except Exception as exc:  # pragma: no cover - sqlite defensive
                logger.emit("store_error", error=str(exc))

        return Response(
            content=body_out,
            status_code=upstream_resp.status_code,
            media_type=content_type,
            headers=resp_headers,
        )

    def _proxy_passthrough(
        method: str,
        path: str,
        body: bytes,
        request: Request,
        kind: str,
        reason: str,
    ) -> Response:
        logger.emit("passthrough", path=path, kind=kind, reason=reason)
        return JSONResponse(
            status_code=400,
            content={"error": {"type": "invalid_request", "message": reason}},
        )

    return app


def _strip_hop_headers(headers: dict[str, str]) -> dict[str, str]:
    hop = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "x-llm-cache",  # internal directive
    }
    return {k: v for k, v in headers.items() if k.lower() not in hop}


def _now() -> float:  # pragma: no cover - trivial
    return time.time()

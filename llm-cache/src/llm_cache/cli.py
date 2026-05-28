"""Command-line interface for llm-cache."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Optional

import click

from llm_cache import __version__
from llm_cache.config import Config, ensure_data_dir, load_config
from llm_cache.store import CacheStore


def _build_config(
    cfg_path: Optional[Path],
    *,
    upstream: Optional[str] = None,
    db_path: Optional[Path] = None,
    ttl: Optional[int] = None,
    max_entries: Optional[int] = None,
    semantic: Optional[bool] = None,
    threshold: Optional[float] = None,
    embedding_model: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> Config:
    cfg = load_config(cfg_path)
    overrides = {
        "upstream": upstream,
        "db_path": db_path,
        "ttl_seconds": ttl,
        "max_entries": max_entries,
        "semantic": semantic,
        "threshold": threshold,
        "embedding_model": embedding_model,
        "host": host,
        "port": port,
    }
    from dataclasses import replace

    clean = {k: v for k, v in overrides.items() if v is not None}
    if clean:
        cfg = replace(cfg, **clean)
    ensure_data_dir(cfg)
    return cfg


@click.group()
@click.version_option(__version__, "--version", prog_name="llm-cache")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Path to config.yaml (default: ~/.llm-cache/config.yaml)",
)
@click.pass_context
def main(ctx: click.Context, config_path: Optional[Path]) -> None:
    """Semantic response cache in front of OpenAI-compatible LLM gateways."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path


@main.command()
@click.option("--host", default=None, help="Listen host (default 127.0.0.1)")
@click.option("--port", type=int, default=None, help="Listen port (default 4118)")
@click.option("--upstream", default=None, help="Upstream URL (default http://localhost:4117)")
@click.option("--db", "db_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--ttl", type=int, default=None, help="TTL in seconds (default 7d)")
@click.option("--max-entries", type=int, default=None, help="Max cache entries (LRU evicts above)")
@click.option("--semantic/--no-semantic", default=None, help="Enable semantic-mode matching")
@click.option("--threshold", type=float, default=None, help="Cosine threshold for semantic hit")
@click.option("--embedding-model", default=None, help="sentence-transformers model name")
@click.pass_context
def serve(
    ctx: click.Context,
    host: Optional[str],
    port: Optional[int],
    upstream: Optional[str],
    db_path: Optional[Path],
    ttl: Optional[int],
    max_entries: Optional[int],
    semantic: Optional[bool],
    threshold: Optional[float],
    embedding_model: Optional[str],
) -> None:
    """Start the caching proxy server."""
    cfg = _build_config(
        ctx.obj.get("config_path"),
        upstream=upstream,
        db_path=db_path,
        ttl=ttl,
        max_entries=max_entries,
        semantic=semantic,
        threshold=threshold,
        embedding_model=embedding_model,
        host=host,
        port=port,
    )
    import uvicorn  # imported here so `--help` does not pay the cost

    from llm_cache.proxy import create_app

    app = create_app(cfg)
    click.echo(
        f"llm-cache serving on http://{cfg.host}:{cfg.port}  "
        f"upstream={cfg.upstream}  semantic={cfg.semantic}"
    )
    uvicorn.run(app, host=cfg.host, port=cfg.port, log_level="info")


@main.command()
@click.option("--json", "as_json", is_flag=True, help="Emit raw JSON")
@click.pass_context
def stats(ctx: click.Context, as_json: bool) -> None:
    """Show cache size and entry counts (local store only).

    Live runtime hit/miss metrics are available via GET /stats on the running server.
    """
    cfg = _build_config(ctx.obj.get("config_path"))
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    try:
        data = store.stats()
        data["db_path"] = str(cfg.db_path)
    finally:
        store.close()
    if as_json:
        click.echo(json.dumps(data, indent=2, sort_keys=True))
        return
    click.echo(f"db          : {data['db_path']}")
    click.echo(f"entries     : {data['entries']}")
    click.echo(f"bytes stored: {data['bytes_stored']}")
    click.echo(f"total hits  : {data['total_hits']}")


@main.command()
@click.option("--expired-only", is_flag=True, help="Only purge expired entries")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def purge(ctx: click.Context, expired_only: bool, yes: bool) -> None:
    """Purge cache entries."""
    cfg = _build_config(ctx.obj.get("config_path"))
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    try:
        if expired_only:
            removed = store.purge_expired()
            click.echo(f"removed {removed} expired entries")
            return
        if not yes:
            if not click.confirm(
                f"This will delete ALL cache entries in {cfg.db_path}. Continue?",
                default=False,
            ):
                click.echo("aborted")
                return
        removed = store.purge_all()
        click.echo(f"removed {removed} entries")
    finally:
        store.close()


@main.command()
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Write JSON to this file (default: stdout)",
)
@click.option("--include-body/--no-include-body", default=True, help="Embed cached response bodies")
@click.pass_context
def export(ctx: click.Context, out_path: Optional[Path], include_body: bool) -> None:
    """Export all cache entries as JSON (NDJSON-friendly when --no-include-body)."""
    cfg = _build_config(ctx.obj.get("config_path"))
    store = CacheStore(cfg.db_path, cfg.ttl_seconds, cfg.max_entries)
    out_fh = out_path.open("w", encoding="utf-8") if out_path else sys.stdout
    try:
        records = []
        for entry in store.iter_all():
            record = {
                "key": entry.key,
                "bucket": entry.bucket,
                "content_type": entry.content_type,
                "created_at": entry.created_at,
                "expires_at": entry.expires_at,
                "last_hit": entry.last_hit,
                "hit_count": entry.hit_count,
                "byte_size": entry.byte_size,
                "prompt": entry.prompt,
                "has_embedding": entry.embedding is not None,
            }
            if include_body:
                record["body_base64"] = base64.b64encode(entry.body).decode("ascii")
            records.append(record)
        json.dump({"entries": records, "count": len(records)}, out_fh, indent=2, sort_keys=True)
        if out_path:
            out_fh.write("\n")
    finally:
        if out_path:
            out_fh.close()
        store.close()


if __name__ == "__main__":  # pragma: no cover
    main()

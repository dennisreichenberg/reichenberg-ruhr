"""Configuration loading.

Config sources (later overrides earlier):
1. Defaults.
2. ~/.llm-cache/config.yaml (if present).
3. Environment variables (LLM_CACHE_*).
4. CLI flags (applied by the caller).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

DEFAULT_UPSTREAM = "http://localhost:4117"
DEFAULT_TTL_SECONDS = 7 * 24 * 3600  # 7 days
DEFAULT_MAX_ENTRIES = 10_000
DEFAULT_THRESHOLD = 0.97
# Aligned with local-rag default (sentence-transformers all-MiniLM-L6-v2).
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_DATA_DIR = Path.home() / ".llm-cache"


@dataclass
class Config:
    upstream: str = DEFAULT_UPSTREAM
    backend: str = "sqlite"  # sqlite or redis
    db_path: Path = field(default_factory=lambda: DEFAULT_DATA_DIR / "cache.sqlite3")
    redis_url: str = "redis://localhost:6379/0"
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    max_entries: int = DEFAULT_MAX_ENTRIES
    semantic: bool = False
    threshold: float = DEFAULT_THRESHOLD
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    log_path: Path = field(default_factory=lambda: DEFAULT_DATA_DIR / "log.jsonl")
    host: str = "127.0.0.1"
    port: int = 4118
    request_timeout: float = 300.0


def _coerce(value: str, target: Any) -> Any:
    if isinstance(target, bool):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(target, int):
        return int(value)
    if isinstance(target, float):
        return float(value)
    if isinstance(target, Path):
        return Path(value).expanduser()
    return value


def load_config(path: Path | None = None) -> Config:
    """Load config from yaml (if present) and overlay environment variables.

    Environment variables use the `LLM_CACHE_<FIELD>` pattern, e.g.
    `LLM_CACHE_UPSTREAM=http://localhost:11434`.
    """
    cfg = Config()
    cfg_path = path or (DEFAULT_DATA_DIR / "config.yaml")
    if cfg_path.exists():
        try:
            raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except Exception:
            raw = {}
        if isinstance(raw, dict):
            updates: dict[str, Any] = {}
            for key, value in raw.items():
                if not hasattr(cfg, key):
                    continue
                target = getattr(cfg, key)
                if isinstance(target, Path) and not isinstance(value, Path):
                    updates[key] = Path(str(value)).expanduser()
                else:
                    updates[key] = value
            cfg = replace(cfg, **updates)

    env_updates: dict[str, Any] = {}
    for fname in cfg.__dataclass_fields__:
        env_key = f"LLM_CACHE_{fname.upper()}"
        if env_key in os.environ:
            current = getattr(cfg, fname)
            env_updates[fname] = _coerce(os.environ[env_key], current)
    if env_updates:
        cfg = replace(cfg, **env_updates)
    return cfg


def ensure_data_dir(cfg: Config) -> None:
    cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.log_path.parent.mkdir(parents=True, exist_ok=True)

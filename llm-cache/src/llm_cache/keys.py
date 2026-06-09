"""Cache-key computation.

Exact match key: SHA256 of canonical-JSON of the cache-relevant request fields.
Semantic key: hash of (model, normalised last user message) plus the embedding
vector is stored separately in the store.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

CHAT_KEY_FIELDS = ("model", "messages", "temperature", "top_p", "max_tokens", "stop", "seed")
EMBEDDING_KEY_FIELDS = ("model", "input", "encoding_format", "dimensions")


def _canonical(payload: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in fields:
        if f in payload:
            out[f] = payload[f]
    return out


def chat_key(payload: dict[str, Any]) -> str:
    canonical = _canonical(payload, CHAT_KEY_FIELDS)
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "chat:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def embedding_key(payload: dict[str, Any]) -> str:
    canonical = _canonical(payload, EMBEDDING_KEY_FIELDS)
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "emb:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def last_user_message(payload: dict[str, Any]) -> str | None:
    """Return the textual content of the last user message, if any.

    Supports both string content and content-parts arrays (extracts text parts).
    """
    msgs = payload.get("messages")
    if not isinstance(msgs, list):
        return None
    for msg in reversed(msgs):
        if not isinstance(msg, dict):
            continue
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content.strip() or None
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text = part.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            if parts:
                return " ".join(parts).strip() or None
        return None
    return None


def semantic_bucket(model: str) -> str:
    """Bucket id used to scope semantic search to a single model."""
    return "sem:" + hashlib.sha256(model.encode("utf-8")).hexdigest()

"""Normalized data model shared by the ingest, store and report layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class UsageRecord:
    """One LLM request, normalized across every backend/log format.

    Tokens default to 0 (some backends do not report them) and ``cost_usd`` is
    filled in by the pricing layer at ingest time so reports stay cheap.
    """

    ts: str  # ISO8601 UTC, e.g. "2026-05-27T10:15:03Z"
    model: str
    backend: str  # ollama | vllm | openai | anthropic | ...
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float | None = None
    cost_usd: float = 0.0
    status: str = "success"  # success | error
    request_id: str | None = None
    source: str | None = None  # log file the record came from

    def as_dict(self) -> dict:
        return asdict(self)

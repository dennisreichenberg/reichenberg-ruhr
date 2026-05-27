"""Parse LLM request logs into normalized UsageRecords.

The tool deliberately does not run a proxy of its own (see README "Abgrenzung").
It consumes log data that llm-gateway / litellm-proxy already produces.

Supported input: newline-delimited JSON (JSONL), one request per line. Two
shapes are understood out of the box and can be mixed in the same file:

  1. LiteLLM "standard logging payload" (what litellm-proxy emits with
     json_logs=true), e.g. keys like ``start_time``, ``end_time``, ``model``,
     ``custom_llm_provider``, ``response_cost`` and a nested ``usage`` object.
  2. A generic/simplified shape with flat keys such as ``timestamp``,
     ``model``, ``backend``, ``prompt_tokens``, ``completion_tokens``,
     ``latency_ms``.

Field lookup is tolerant: each logical field is pulled from the first key that
is present, so minor format drift does not break ingestion. Lines that are
blank, not JSON, or carry no model are skipped (and counted) rather than
aborting the whole import.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable, Iterator

from llm_usage.models import UsageRecord
from llm_usage.pricing import PricingTable


class IngestStats:
    """Counters returned from an ingest pass."""

    def __init__(self) -> None:
        self.parsed = 0
        self.skipped = 0

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"IngestStats(parsed={self.parsed}, skipped={self.skipped})"


def parse_lines(
    lines: Iterable[str],
    pricing: PricingTable,
    source: str | None = None,
    stats: IngestStats | None = None,
) -> Iterator[UsageRecord]:
    """Yield a UsageRecord for every parseable JSON line."""
    stats = stats if stats is not None else IngestStats()
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            stats.skipped += 1
            continue
        if not isinstance(obj, dict):
            stats.skipped += 1
            continue
        record = record_from_dict(obj, pricing, source=source)
        if record is None:
            stats.skipped += 1
            continue
        stats.parsed += 1
        yield record


def record_from_dict(
    obj: dict, pricing: PricingTable, source: str | None = None
) -> UsageRecord | None:
    """Build one normalized record from a raw log object, or None if unusable."""
    model = _first(obj, "model", "model_group", "model_name", "request_model")
    if not model:
        return None
    model = str(model)

    usage = obj.get("usage") if isinstance(obj.get("usage"), dict) else {}

    prompt = _to_int(_first(obj, "prompt_tokens", "input_tokens") or usage.get("prompt_tokens"))
    completion = _to_int(
        _first(obj, "completion_tokens", "output_tokens") or usage.get("completion_tokens")
    )
    total = _to_int(_first(obj, "total_tokens") or usage.get("total_tokens"))
    if not total:
        total = prompt + completion

    backend = _first(obj, "backend", "custom_llm_provider", "litellm_provider", "provider")
    backend = str(backend).lower() if backend else _infer_backend(model)

    start = _first(obj, "start_time", "startTime", "timestamp", "ts", "time", "created_at")
    end = _first(obj, "end_time", "endTime")
    ts = _normalize_ts(start)

    latency = _first(obj, "latency_ms", "response_ms", "duration_ms")
    if latency is not None:
        latency_ms: float | None = _to_float(latency)
    else:
        latency_ms = _latency_from_span(start, end)

    status = _first(obj, "status")
    if status is None:
        # LiteLLM marks failures with an "exception"/"error" key.
        status = "error" if (obj.get("exception") or obj.get("error")) else "success"
    status = "error" if str(status).lower() in {"error", "failure", "failed"} else "success"

    cost = _first(obj, "response_cost", "cost", "cost_usd", "spend")
    if cost is not None:
        cost_usd = round(_to_float(cost), 6)
    else:
        cost_usd = pricing.estimate(model, prompt, completion, backend=backend)

    request_id = _first(obj, "request_id", "id", "litellm_call_id", "call_id")

    return UsageRecord(
        ts=ts,
        model=model,
        backend=backend,
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        status=status,
        request_id=str(request_id) if request_id is not None else None,
        source=source,
    )


# --- helpers ----------------------------------------------------------------


def _first(obj: dict, *keys: str):
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    return None


def _infer_backend(model: str) -> str:
    low = model.lower()
    if "/" in low:
        prefix = low.split("/", 1)[0]
        if prefix in {"ollama", "vllm", "openai", "anthropic", "azure", "gemini", "bedrock"}:
            return prefix
    if low.startswith(("gpt-", "o1", "o3")):
        return "openai"
    if low.startswith("claude"):
        return "anthropic"
    if low.startswith("gemini"):
        return "gemini"
    return "unknown"


def _to_int(value) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_ts(value) -> str:
    """Return an ISO8601 UTC string 'YYYY-MM-DDTHH:MM:SSZ' for any input."""
    dt = _parse_dt(value)
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Epoch seconds, or milliseconds if the magnitude is large.
        secs = value / 1000.0 if value > 1e12 else float(value)
        return datetime.fromtimestamp(secs, tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.fromtimestamp(float(text), tz=timezone.utc)
            except ValueError:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return None


def _latency_from_span(start, end) -> float | None:
    start_dt = _parse_dt(start)
    end_dt = _parse_dt(end)
    if start_dt is None or end_dt is None:
        return None
    delta = (end_dt - start_dt).total_seconds() * 1000.0
    return round(delta, 3) if delta >= 0 else None

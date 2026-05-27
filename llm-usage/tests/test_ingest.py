"""Tests for log parsing / normalization."""

import json

from llm_usage.ingest import IngestStats, parse_lines, record_from_dict
from llm_usage.pricing import PricingTable


def _pricing():
    return PricingTable(
        {
            "backends": {"ollama": {"input": 0, "output": 0}},
            "models": {"gpt-4o": {"input": 2.5, "output": 10.0}},
        }
    )


def test_litellm_payload_with_nested_usage():
    obj = {
        "litellm_call_id": "abc",
        "start_time": "2026-05-20T08:01:12Z",
        "end_time": "2026-05-20T08:01:13.500Z",
        "model": "gpt-4o",
        "custom_llm_provider": "openai",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    rec = record_from_dict(obj, _pricing())
    assert rec.model == "gpt-4o"
    assert rec.backend == "openai"
    assert rec.prompt_tokens == 100
    assert rec.completion_tokens == 50
    assert rec.total_tokens == 150
    assert rec.request_id == "abc"
    assert rec.latency_ms == 1500.0
    assert rec.cost_usd == round((100 * 2.5 + 50 * 10.0) / 1_000_000, 6)


def test_existing_cost_is_preferred_over_estimate():
    obj = {"model": "gpt-4o", "prompt_tokens": 100, "completion_tokens": 50, "response_cost": 0.42}
    rec = record_from_dict(obj, _pricing())
    assert rec.cost_usd == 0.42


def test_backend_inferred_from_model_prefix():
    rec = record_from_dict({"model": "ollama/llama3:8b", "usage": {}}, _pricing())
    assert rec.backend == "ollama"
    assert rec.cost_usd == 0.0


def test_total_tokens_derived_when_missing():
    rec = record_from_dict(
        {"model": "x", "prompt_tokens": 10, "completion_tokens": 5}, _pricing()
    )
    assert rec.total_tokens == 15


def test_error_status_from_exception():
    rec = record_from_dict({"model": "gpt-4o", "exception": "Boom"}, _pricing())
    assert rec.status == "error"


def test_generic_flat_shape():
    obj = {
        "timestamp": "2026-05-23T12:00:00Z",
        "model": "mistral:7b",
        "backend": "ollama",
        "prompt_tokens": 20,
        "completion_tokens": 8,
        "latency_ms": 740.5,
    }
    rec = record_from_dict(obj, _pricing())
    assert rec.backend == "ollama"
    assert rec.latency_ms == 740.5


def test_missing_model_is_skipped():
    assert record_from_dict({"usage": {"prompt_tokens": 5}}, _pricing()) is None


def test_parse_lines_skips_garbage_and_counts():
    lines = [
        "",
        "not json",
        json.dumps({"model": "gpt-4o", "prompt_tokens": 1, "completion_tokens": 1}),
        json.dumps({"no_model": True}),
        "[1, 2, 3]",  # valid json but not a dict
    ]
    stats = IngestStats()
    records = list(parse_lines(lines, _pricing(), source="t", stats=stats))
    assert len(records) == 1
    assert stats.parsed == 1
    # skipped: "not json" + dict without model + the non-dict JSON array (blank is ignored)
    assert stats.skipped == 3
    assert records[0].source == "t"

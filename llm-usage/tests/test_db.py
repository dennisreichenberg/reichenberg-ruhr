"""Tests for the SQLite store and aggregation queries."""

import pytest

from llm_usage.db import UsageStore
from llm_usage.models import UsageRecord


def _store(tmp_path):
    return UsageStore(tmp_path / "usage.db")


def _rec(**kw):
    base = dict(ts="2026-05-20T08:00:00Z", model="gpt-4o", backend="openai")
    base.update(kw)
    return UsageRecord(**base)


def test_insert_and_count(tmp_path):
    with _store(tmp_path) as store:
        added = store.insert_many([_rec(request_id="a"), _rec(request_id="b")])
        assert added == 2
        assert store.count() == 2


def test_dedup_by_request_id(tmp_path):
    with _store(tmp_path) as store:
        store.insert_many([_rec(request_id="dup")])
        added = store.insert_many([_rec(request_id="dup"), _rec(request_id="new")])
        assert added == 1
        assert store.count() == 2


def test_null_request_id_not_deduped(tmp_path):
    with _store(tmp_path) as store:
        store.insert_many([_rec(request_id=None), _rec(request_id=None)])
        assert store.count() == 2


def test_aggregate_by_model(tmp_path):
    with _store(tmp_path) as store:
        store.insert_many(
            [
                _rec(request_id="1", model="gpt-4o", total_tokens=100, cost_usd=0.5),
                _rec(request_id="2", model="gpt-4o", total_tokens=200, cost_usd=1.0),
                _rec(request_id="3", model="llama3:8b", backend="ollama", total_tokens=50),
            ]
        )
        rows = store.aggregate(by="model")
        by_model = {r["bucket"]: r for r in rows}
        assert by_model["gpt-4o"]["requests"] == 2
        assert by_model["gpt-4o"]["total_tokens_sum"] == 300
        assert by_model["gpt-4o"]["cost_usd_sum"] == 1.5
        # Ordered by cost desc -> gpt-4o first.
        assert rows[0]["bucket"] == "gpt-4o"


def test_aggregate_by_day_and_backend(tmp_path):
    with _store(tmp_path) as store:
        store.insert_many(
            [
                _rec(request_id="1", ts="2026-05-20T08:00:00Z", backend="openai"),
                _rec(request_id="2", ts="2026-05-21T08:00:00Z", backend="ollama"),
            ]
        )
        days = {r["bucket"] for r in store.aggregate(by="day")}
        assert days == {"2026-05-20", "2026-05-21"}
        backends = {r["bucket"] for r in store.aggregate(by="backend")}
        assert backends == {"openai", "ollama"}


def test_time_range_filter(tmp_path):
    with _store(tmp_path) as store:
        store.insert_many(
            [
                _rec(request_id="1", ts="2026-05-20T08:00:00Z"),
                _rec(request_id="2", ts="2026-05-25T08:00:00Z"),
            ]
        )
        rows = store.aggregate(by="model", since="2026-05-22T00:00:00Z")
        assert sum(r["requests"] for r in rows) == 1


def test_top_metric_and_errors(tmp_path):
    with _store(tmp_path) as store:
        store.insert_many(
            [
                _rec(request_id="1", model="cheap", total_tokens=10, cost_usd=0.01),
                _rec(request_id="2", model="pricey", total_tokens=5, cost_usd=5.0, status="error"),
            ]
        )
        top_cost = store.top(metric="cost", limit=1)
        assert top_cost[0]["bucket"] == "pricey"
        assert top_cost[0]["errors"] == 1
        top_tokens = store.top(metric="tokens", limit=1)
        assert top_tokens[0]["bucket"] == "cheap"


def test_invalid_dimension_raises(tmp_path):
    with _store(tmp_path) as store:
        with pytest.raises(ValueError):
            store.aggregate(by="nonsense")
        with pytest.raises(ValueError):
            store.top(metric="nonsense")


def test_records_export_order(tmp_path):
    with _store(tmp_path) as store:
        store.insert_many(
            [
                _rec(request_id="late", ts="2026-05-25T08:00:00Z"),
                _rec(request_id="early", ts="2026-05-20T08:00:00Z"),
            ]
        )
        rows = store.records()
        assert [r["request_id"] for r in rows] == ["early", "late"]

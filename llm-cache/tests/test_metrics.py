from llm_cache.metrics import MetricsRegistry


def test_metrics_counts_and_rate() -> None:
    m = MetricsRegistry()
    m.hit_exact(120)
    m.hit_semantic(80)
    m.miss()
    snap = m.snapshot()
    assert snap["hits_exact"] == 1
    assert snap["hits_semantic"] == 1
    assert snap["misses"] == 1
    assert snap["total_requests"] == 3
    assert snap["hit_rate"] == 2 / 3
    assert snap["bytes_saved"] == 200
    assert snap["tokens_saved_estimate"] >= 1


def test_zero_requests() -> None:
    m = MetricsRegistry()
    snap = m.snapshot()
    assert snap["total_requests"] == 0
    assert snap["hit_rate"] == 0.0

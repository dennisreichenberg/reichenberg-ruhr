import time

from llm_cache.store import CacheStore, cosine


def test_cosine_basic() -> None:
    assert cosine([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine([1.0, 1.0], [1.0, 1.0]) > 0.999


def test_put_get_roundtrip(tmp_path) -> None:
    import pytest

    store = CacheStore(tmp_path / "c.sqlite", ttl_seconds=60, max_entries=100)
    try:
        store.put(
            key="k1",
            bucket="b1",
            body=b'{"ok": true}',
            content_type="application/json",
            prompt="hi",
            embedding=[0.1, 0.2, 0.3],
        )
        hit = store.get("k1")
        assert hit is not None
        assert hit.body == b'{"ok": true}'
        assert hit.hit_count == 1
        assert hit.embedding == pytest.approx([0.1, 0.2, 0.3], rel=1e-4, abs=1e-6)
    finally:
        store.close()


def test_ttl_expiry(tmp_path) -> None:
    store = CacheStore(tmp_path / "c.sqlite", ttl_seconds=1, max_entries=100)
    try:
        store.put("k", "b", b"x", "text/plain")
        # Manually advance "now" via the get/put now= parameter.
        future = time.time() + 5
        assert store.get("k", now=future) is None
    finally:
        store.close()


def test_lru_eviction(tmp_path) -> None:
    store = CacheStore(tmp_path / "c.sqlite", ttl_seconds=60, max_entries=3)
    try:
        for i in range(5):
            store.put(f"k{i}", "b", f"v{i}".encode(), "text/plain")
        stats = store.stats()
        assert stats["entries"] == 3
    finally:
        store.close()


def test_semantic_lookup(tmp_path) -> None:
    store = CacheStore(tmp_path / "c.sqlite", ttl_seconds=60, max_entries=10)
    try:
        store.put(
            key="k-target",
            bucket="bucket-a",
            body=b"hit",
            content_type="text/plain",
            prompt="hello world",
            embedding=[1.0, 0.0, 0.0],
        )
        store.put(
            key="k-other",
            bucket="bucket-a",
            body=b"miss",
            content_type="text/plain",
            prompt="goodbye",
            embedding=[0.0, 1.0, 0.0],
        )
        # very similar to k-target
        result = store.semantic_lookup("bucket-a", [0.99, 0.01, 0.0], threshold=0.95)
        assert result is not None
        entry, sim = result
        assert entry.key == "k-target"
        assert sim > 0.95

        # different bucket: no match
        assert store.semantic_lookup("bucket-b", [1.0, 0.0, 0.0], threshold=0.95) is None

        # below threshold: no match
        assert (
            store.semantic_lookup("bucket-a", [0.0, 0.0, 1.0], threshold=0.9) is None
        )
    finally:
        store.close()


def test_purge_all_and_expired(tmp_path) -> None:
    store = CacheStore(tmp_path / "c.sqlite", ttl_seconds=1, max_entries=10)
    try:
        store.put("k1", "b", b"x", "text/plain")
        store.put("k2", "b", b"y", "text/plain")
        # Force one entry expired
        store._conn.execute(
            "UPDATE entries SET expires_at = ? WHERE key = ?",
            (time.time() - 10, "k2"),
        )
        removed = store.purge_expired()
        assert removed == 1
        removed = store.purge_all()
        assert removed == 1
        assert store.stats()["entries"] == 0
    finally:
        store.close()


from llm_cache.config import Config, load_config


def test_defaults_have_expected_shape() -> None:
    cfg = Config()
    assert cfg.upstream.startswith("http://")
    assert cfg.ttl_seconds == 7 * 24 * 3600
    assert cfg.threshold == 0.97
    assert cfg.semantic is False


def test_yaml_overlay(tmp_path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "upstream: http://example.invalid:1234\n"
        "ttl_seconds: 60\n"
        "semantic: true\n",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg.upstream == "http://example.invalid:1234"
    assert cfg.ttl_seconds == 60
    assert cfg.semantic is True


def test_env_overlay(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LLM_CACHE_UPSTREAM", "http://env.invalid:9999")
    monkeypatch.setenv("LLM_CACHE_TTL_SECONDS", "42")
    monkeypatch.setenv("LLM_CACHE_SEMANTIC", "yes")
    cfg = load_config(tmp_path / "does-not-exist.yaml")
    assert cfg.upstream == "http://env.invalid:9999"
    assert cfg.ttl_seconds == 42
    assert cfg.semantic is True

import json

from click.testing import CliRunner

from llm_cache.cli import main


def test_version() -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["--version"])
    assert res.exit_code == 0
    assert "llm-cache" in res.output


def test_stats_empty(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_CACHE_DB_PATH", str(tmp_path / "c.sqlite"))
    monkeypatch.setenv("LLM_CACHE_LOG_PATH", str(tmp_path / "log.jsonl"))
    runner = CliRunner()
    res = runner.invoke(main, ["stats", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["entries"] == 0


def test_purge_expired_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_CACHE_DB_PATH", str(tmp_path / "c.sqlite"))
    monkeypatch.setenv("LLM_CACHE_LOG_PATH", str(tmp_path / "log.jsonl"))
    runner = CliRunner()
    res = runner.invoke(main, ["purge", "--expired-only"])
    assert res.exit_code == 0
    assert "removed 0" in res.output


def test_export_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_CACHE_DB_PATH", str(tmp_path / "c.sqlite"))
    monkeypatch.setenv("LLM_CACHE_LOG_PATH", str(tmp_path / "log.jsonl"))
    runner = CliRunner()
    res = runner.invoke(main, ["export"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["count"] == 0
    assert data["entries"] == []

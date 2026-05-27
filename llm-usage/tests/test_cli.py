"""End-to-end CLI tests via Click's test runner against the example log."""

import json
from pathlib import Path

from click.testing import CliRunner

from llm_usage.cli import cli

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample-litellm.jsonl"


def _ingest(runner, db):
    return runner.invoke(cli, ["ingest", str(EXAMPLE), "--db", str(db)])


def test_ingest_then_report(tmp_path):
    runner = CliRunner()
    db = tmp_path / "usage.db"

    res = _ingest(runner, db)
    assert res.exit_code == 0, res.output
    assert "Ingested 10 record(s)" in res.output

    res = runner.invoke(cli, ["report", "--db", str(db)])
    assert res.exit_code == 0, res.output
    assert "gpt-4o" in res.output
    assert "TOTAL" in res.output


def test_report_json_aggregates_real_costs(tmp_path):
    runner = CliRunner()
    db = tmp_path / "usage.db"
    _ingest(runner, db)

    res = runner.invoke(cli, ["report", "--db", str(db), "--by", "backend", "--json"])
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    backends = {r["bucket"] for r in payload["rows"]}
    assert {"ollama", "openai", "anthropic", "vllm"} <= backends
    # Local backends cost nothing; cloud ones must have a positive estimate.
    by_bucket = {r["bucket"]: r for r in payload["rows"]}
    assert by_bucket["ollama"]["cost_usd_sum"] == 0.0
    assert by_bucket["anthropic"]["cost_usd_sum"] > 0.0


def test_ingest_is_idempotent(tmp_path):
    runner = CliRunner()
    db = tmp_path / "usage.db"
    _ingest(runner, db)
    res = _ingest(runner, db)  # second pass: same request ids
    assert "added 0 new" in res.output


def test_top_by_cost(tmp_path):
    runner = CliRunner()
    db = tmp_path / "usage.db"
    _ingest(runner, db)

    res = runner.invoke(cli, ["top", "--db", str(db), "--metric", "cost", "--json"])
    assert res.exit_code == 0, res.output
    rows = json.loads(res.output)["rows"]
    costs = [r["cost_usd_sum"] for r in rows]
    assert costs == sorted(costs, reverse=True)


def test_export_csv(tmp_path):
    runner = CliRunner()
    db = tmp_path / "usage.db"
    _ingest(runner, db)

    res = runner.invoke(cli, ["export", "--db", str(db), "--format", "csv"])
    assert res.exit_code == 0, res.output
    lines = [ln for ln in res.output.splitlines() if ln.strip()]
    assert lines[0].startswith("request_id,ts,model,backend")
    assert len(lines) == 11  # header + 10 records


def test_since_until_filter(tmp_path):
    runner = CliRunner()
    db = tmp_path / "usage.db"
    _ingest(runner, db)

    res = runner.invoke(
        cli,
        ["report", "--db", str(db), "--since", "2026-05-21", "--until", "2026-05-21", "--json"],
    )
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    # Only the three 2026-05-21 requests fall in range.
    assert sum(r["requests"] for r in payload["rows"]) == 3


def test_empty_db_report(tmp_path):
    runner = CliRunner()
    res = runner.invoke(cli, ["report", "--db", str(tmp_path / "empty.db")])
    assert res.exit_code == 0
    assert "No usage data" in res.output

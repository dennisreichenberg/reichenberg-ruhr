"""Click command-line interface for llm-usage.

Commands:
  ingest   read JSONL request logs (or stdin) into the SQLite store
  report   aggregate usage by model / backend / day for a time range
  top      rank the biggest consumers by cost / tokens / requests
  export   dump raw stored records as JSON or CSV
"""

from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime, time, timezone
from pathlib import Path

import click

from llm_usage import __version__
from llm_usage.db import UsageStore, default_db_path
from llm_usage.ingest import IngestStats, parse_lines
from llm_usage.pricing import PricingTable

_DB_OPTION = click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="SQLite file (default: $LLM_USAGE_DB or ~/.llm-usage/usage.db).",
)
_SINCE_OPTION = click.option("--since", default=None, help="Start of range, e.g. 2026-05-01.")
_UNTIL_OPTION = click.option(
    "--until", default=None, help="End of range (inclusive), e.g. 2026-05-31."
)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="llm-usage")
def cli() -> None:
    """Historical request and cost accounting across all LLM backends."""


@cli.command()
@click.argument("logfiles", nargs=-1, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@_DB_OPTION
@click.option(
    "--pricing",
    "pricing_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="YAML price table (default: packaged pricing.yaml).",
)
@click.option("--stdin", "use_stdin", is_flag=True, help="Read JSONL from standard input.")
def ingest(logfiles, db_path, pricing_path, use_stdin) -> None:
    """Read request logs (LiteLLM JSONL or generic JSONL) into the store."""
    if not logfiles and not use_stdin:
        raise click.UsageError("Pass one or more LOGFILES, or --stdin.")

    pricing = PricingTable.load(pricing_path)
    db_path = db_path or default_db_path()
    stats = IngestStats()
    inserted = 0

    with UsageStore(db_path) as store:
        if use_stdin:
            records = parse_lines(sys.stdin, pricing, source="<stdin>", stats=stats)
            inserted += store.insert_many(records)
        for logfile in logfiles:
            with open(logfile, "r", encoding="utf-8") as fh:
                records = parse_lines(fh, pricing, source=str(logfile), stats=stats)
                inserted += store.insert_many(records)
        total = store.count()

    click.echo(
        f"Ingested {stats.parsed} record(s), skipped {stats.skipped}, "
        f"added {inserted} new ({total} total in {db_path})."
    )


@cli.command()
@_DB_OPTION
@click.option(
    "--by",
    type=click.Choice(["model", "backend", "day"]),
    default="model",
    help="Aggregation dimension.",
)
@_SINCE_OPTION
@_UNTIL_OPTION
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of a table.")
def report(db_path, by, since, until, as_json) -> None:
    """Aggregate usage by model, backend or day."""
    db_path = db_path or default_db_path()
    since_n, until_n = _norm_since(since), _norm_until(until)
    with UsageStore(db_path) as store:
        rows = store.aggregate(by=by, since=since_n, until=until_n)

    if as_json:
        payload = {"by": by, "since": since_n, "until": until_n, "rows": rows}
        click.echo(json.dumps(payload, indent=2))
        return

    if not rows:
        click.echo("No usage data for the selected range.")
        return

    headers = [by, "requests", "prompt", "completion", "total", "avg_ms", "cost_usd", "errors"]
    table = [
        [
            r["bucket"],
            r["requests"],
            r["prompt_tokens_sum"],
            r["completion_tokens_sum"],
            r["total_tokens_sum"],
            "-" if r["latency_ms_avg"] is None else f"{r['latency_ms_avg']:.0f}",
            f"{r['cost_usd_sum']:.4f}",
            r["errors"],
        ]
        for r in rows
    ]
    totals = [
        "TOTAL",
        sum(r["requests"] for r in rows),
        sum(r["prompt_tokens_sum"] for r in rows),
        sum(r["completion_tokens_sum"] for r in rows),
        sum(r["total_tokens_sum"] for r in rows),
        "",
        f"{sum(r['cost_usd_sum'] for r in rows):.4f}",
        sum(r["errors"] for r in rows),
    ]
    click.echo(_render_table(headers, table, footer=totals))


@cli.command()
@_DB_OPTION
@click.option(
    "--metric",
    type=click.Choice(["cost", "tokens", "requests"]),
    default="cost",
    help="Ranking metric.",
)
@click.option(
    "--by",
    type=click.Choice(["model", "backend"]),
    default="model",
    help="Group consumers by model or backend.",
)
@click.option("--limit", type=int, default=10, show_default=True, help="How many rows to show.")
@_SINCE_OPTION
@_UNTIL_OPTION
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of a table.")
def top(db_path, metric, by, limit, since, until, as_json) -> None:
    """Show the biggest consumers (default: by cost)."""
    db_path = db_path or default_db_path()
    since_n, until_n = _norm_since(since), _norm_until(until)
    with UsageStore(db_path) as store:
        rows = store.top(metric=metric, limit=limit, by=by, since=since_n, until=until_n)

    if as_json:
        click.echo(json.dumps({"metric": metric, "by": by, "rows": rows}, indent=2))
        return

    if not rows:
        click.echo("No usage data for the selected range.")
        return

    headers = [by, "requests", "total_tokens", "cost_usd"]
    table = [
        [r["bucket"], r["requests"], r["total_tokens_sum"], f"{r['cost_usd_sum']:.4f}"]
        for r in rows
    ]
    click.echo(_render_table(headers, table))


@cli.command()
@_DB_OPTION
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Output format.",
)
@_SINCE_OPTION
@_UNTIL_OPTION
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write to a file instead of stdout.",
)
def export(db_path, fmt, since, until, output) -> None:
    """Export raw stored records as JSON or CSV."""
    db_path = db_path or default_db_path()
    since_n, until_n = _norm_since(since), _norm_until(until)
    with UsageStore(db_path) as store:
        rows = store.records(since=since_n, until=until_n)

    if fmt == "json":
        text = json.dumps(rows, indent=2)
    else:
        text = _to_csv(rows)

    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Wrote {len(rows)} record(s) to {output}.")
    else:
        click.echo(text)


# --- helpers ----------------------------------------------------------------


def _norm_since(value: str | None) -> str | None:
    return _norm_bound(value, end_of_day=False)


def _norm_until(value: str | None) -> str | None:
    return _norm_bound(value, end_of_day=True)


def _norm_bound(value: str | None, end_of_day: bool) -> str | None:
    """Normalize a --since/--until value to the store's 'YYYY-MM-DDTHH:MM:SSZ' form.

    A bare date on --until expands to end-of-day so the bound is inclusive.
    """
    if not value:
        return None
    text = value.strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        date_only = len(text) == 10
    except ValueError:
        raise click.BadParameter(f"could not parse date/time: {value!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if date_only and end_of_day:
        dt = datetime.combine(dt.date(), time(23, 59, 59), tzinfo=dt.tzinfo)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_csv(rows: list[dict]) -> str:
    fields = [
        "request_id", "ts", "model", "backend", "prompt_tokens", "completion_tokens",
        "total_tokens", "latency_ms", "cost_usd", "status", "source",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k) for k in fields})
    return buf.getvalue()


def _render_table(headers: list[str], rows: list[list], footer: list | None = None) -> str:
    """Minimal dependency-free fixed-width table renderer."""
    cols = list(zip(*([headers] + rows + ([footer] if footer else []))))
    widths = [max(len(str(cell)) for cell in col) for col in cols]

    def fmt_row(cells: list) -> str:
        return "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(cells))

    lines = [fmt_row(headers), "  ".join("-" * w for w in widths)]
    lines += [fmt_row(r) for r in rows]
    if footer:
        lines.append("  ".join("-" * w for w in widths))
        lines.append(fmt_row(footer))
    return "\n".join(lines)

from __future__ import annotations

from collections import deque

from textual.app import ComposeResult
from textual.widgets import Sparkline, Static

MAX_POINTS = 60


class ThroughputGraph(Static):
    DEFAULT_CSS = """
    ThroughputGraph {
        height: auto;
        min-height: 8;
        border: solid cyan;
    }
    ThroughputGraph Sparkline {
        height: 5;
    }
    ThroughputGraph .label {
        text-style: bold;
        color: cyan;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._model_counts: deque[float] = deque(maxlen=MAX_POINTS)

    def compose(self) -> ComposeResult:
        yield Static("Throughput (active models over time)", classes="label")
        yield Sparkline([], id="throughput-spark")

    def push_value(self, count: float) -> None:
        self._model_counts.append(count)
        spark = self.query_one(Sparkline)
        spark.data = list(self._model_counts)

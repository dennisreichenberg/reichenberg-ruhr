from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static


class LatencyPanel(Static):
    DEFAULT_CSS = """
    LatencyPanel {
        height: auto;
        min-height: 6;
        border: solid yellow;
    }
    LatencyPanel .title {
        text-style: bold;
        color: yellow;
    }
    LatencyPanel .metrics {
        margin-left: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("System Metrics", classes="title")
        yield Static("Loading...", id="metrics-content", classes="metrics")

    def update_metrics(
        self,
        *,
        ram_used: str,
        ram_total: str,
        gpus: list | None = None,
        gpu_available: bool = False,
        model_count: int = 0,
    ) -> None:
        lines = [f"RAM: {ram_used} / {ram_total} GB"]
        if gpu_available and gpus:
            for i, gpu in enumerate(gpus):
                lines.append(
                    f"GPU {i}: {gpu.name} -- "
                    f"{gpu.memory_used_gb} / {gpu.memory_total_gb} GB "
                    f"({gpu.utilization_pct}%)"
                )
        elif not gpu_available:
            lines.append("GPU: nvidia-smi not found (CPU mode)")
        else:
            lines.append("GPU: no devices detected")
        lines.append(f"Active models: {model_count}")
        content = self.query_one("#metrics-content", Static)
        content.update("\n".join(lines))

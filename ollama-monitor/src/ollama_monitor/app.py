from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static

from .api import OllamaClient
from .config import Config
from .gpu import get_system_metrics
from .widgets import LatencyPanel, ModelsTable, ThroughputGraph


class OllamaMonitorApp(App):
    TITLE = "ollama-monitor"
    SUB_TITLE = "Real-time Ollama Dashboard"

    CSS = """
    Screen {
        layout: vertical;
    }
    #status-bar {
        dock: top;
        height: 1;
        background: $primary-background;
        color: $text-muted;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_now", "Refresh"),
        Binding("p", "toggle_pause", "Pause"),
    ]

    def __init__(self, config: Config | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config or Config.load()
        self._client = OllamaClient(self.config)
        self._paused = False
        self._timer = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Connecting...", id="status-bar")
        with Vertical():
            yield ModelsTable()
            yield ThroughputGraph()
            yield LatencyPanel()
        yield Footer()

    def on_mount(self) -> None:
        self._timer = self.set_interval(
            self.config.refresh_interval,
            self._poll,
        )
        self.call_later(self._poll)

    async def _poll(self) -> None:
        if self._paused:
            return
        status = await self._client.get_running_models()
        status_bar = self.query_one("#status-bar", Static)
        if status.error:
            status_bar.update(f"Error: {status.error}")
        else:
            status_bar.update(
                f"Connected to {self.config.base_url} -- "
                f"{len(status.models)} model(s) running"
            )

        models_table = self.query_one(ModelsTable)
        models_table.update_models(status.models)

        throughput = self.query_one(ThroughputGraph)
        throughput.push_value(float(len(status.models)))

        sys_metrics = get_system_metrics()
        latency = self.query_one(LatencyPanel)
        latency.update_metrics(
            ram_used=sys_metrics.ram_used_gb,
            ram_total=sys_metrics.ram_total_gb,
            gpus=sys_metrics.gpus,
            gpu_available=sys_metrics.gpu_available,
            model_count=len(status.models),
        )

    def action_refresh_now(self) -> None:
        self.call_later(self._poll)

    def action_toggle_pause(self) -> None:
        self._paused = not self._paused
        status_bar = self.query_one("#status-bar", Static)
        if self._paused:
            status_bar.update("PAUSED -- press 'p' to resume")
        else:
            self.call_later(self._poll)

    async def on_unmount(self) -> None:
        await self._client.close()

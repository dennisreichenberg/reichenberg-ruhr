from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static


class ModelsTable(Static):
    DEFAULT_CSS = """
    ModelsTable {
        height: auto;
        max-height: 40%;
        border: solid green;
    }
    ModelsTable DataTable {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        table = DataTable(id="models-table")
        table.add_columns("Model", "Size", "VRAM", "Expires At")
        yield table

    def update_models(self, models: list) -> None:
        table = self.query_one(DataTable)
        table.clear()
        for m in models:
            table.add_row(m.name, m.size_gb, m.vram_gb, m.expires_at or "--")
        if not models:
            table.add_row("(no running models)", "--", "--", "--")

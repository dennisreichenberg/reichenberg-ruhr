from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ollama_monitor.api import ModelInfo, OllamaStatus
from ollama_monitor.app import OllamaMonitorApp
from ollama_monitor.config import Config


@pytest.fixture
def config():
    return Config(host="127.0.0.1", port=11434, refresh_interval=60.0)


MOCK_STATUS = OllamaStatus(
    models=[
        ModelInfo(
            name="llama3.1:8b",
            size=4_920_000_000,
            vram=4_920_000_000,
            expires_at="2026-05-21T12:00:00Z",
        )
    ]
)

MOCK_EMPTY_STATUS = OllamaStatus(models=[])


class TestOllamaMonitorApp:
    @pytest.mark.asyncio
    async def test_app_mounts(self, config):
        app = OllamaMonitorApp(config=config)
        async with app.run_test(size=(120, 40)):
            assert app.title == "ollama-monitor"
            assert app.query_one("#status-bar") is not None

    @pytest.mark.asyncio
    async def test_pause_toggle(self, config):
        app = OllamaMonitorApp(config=config)
        async with app.run_test(size=(120, 40)) as pilot:
            assert app._paused is False
            await pilot.press("p")
            assert app._paused is True
            await pilot.press("p")
            assert app._paused is False

    @pytest.mark.asyncio
    async def test_poll_updates_ui(self, config):
        app = OllamaMonitorApp(config=config)
        with patch.object(
            app._client, "get_running_models", new_callable=AsyncMock, return_value=MOCK_STATUS
        ):
            async with app.run_test(size=(120, 40)):
                await app._poll()
                from ollama_monitor.widgets import ModelsTable

                table = app.query_one(ModelsTable)
                assert table is not None

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ollama_monitor.api import ModelInfo, OllamaClient
from ollama_monitor.config import Config

MOCK_PS_RESPONSE = {
    "models": [
        {
            "name": "llama3.1:8b",
            "size": 4_920_000_000,
            "size_vram": 4_920_000_000,
            "expires_at": "2026-05-21T12:00:00Z",
            "digest": "abc123",
            "details": {"family": "llama"},
        },
        {
            "name": "mistral:7b",
            "size": 4_100_000_000,
            "size_vram": 3_800_000_000,
            "expires_at": "2026-05-21T13:00:00Z",
            "digest": "def456",
            "details": {"family": "mistral"},
        },
    ]
}


@pytest.fixture
def config():
    return Config(host="127.0.0.1", port=11434, refresh_interval=2.0)


@pytest.fixture
def client(config):
    return OllamaClient(config)


class TestModelInfo:
    def test_size_gb(self):
        m = ModelInfo(name="test", size=4_920_000_000, vram=4_920_000_000, expires_at="")
        assert m.size_gb == "4.6 GB"

    def test_vram_gb(self):
        m = ModelInfo(name="test", size=0, vram=8_000_000_000, expires_at="")
        assert m.vram_gb == "7.5 GB"


class TestOllamaClient:
    @pytest.mark.asyncio
    async def test_get_running_models_success(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_PS_RESPONSE
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client._client, "get", new=AsyncMock(return_value=mock_response)
        ):
            status = await client.get_running_models()

        assert status.error is None
        assert len(status.models) == 2
        assert status.models[0].name == "llama3.1:8b"
        assert status.models[1].name == "mistral:7b"

    @pytest.mark.asyncio
    async def test_get_running_models_empty(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client._client, "get", new=AsyncMock(return_value=mock_response)
        ):
            status = await client.get_running_models()

        assert status.error is None
        assert len(status.models) == 0

    @pytest.mark.asyncio
    async def test_get_running_models_connection_error(self, client):
        import httpx

        with patch.object(
            client._client,
            "get",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            status = await client.get_running_models()

        assert status.error is not None
        assert "Connection refused" in status.error

from __future__ import annotations

import tempfile
from pathlib import Path

from ollama_monitor.config import Config


class TestConfig:
    def test_defaults(self):
        config = Config()
        assert config.host == "127.0.0.1"
        assert config.port == 11434
        assert config.refresh_interval == 2.0

    def test_base_url(self):
        config = Config(host="192.168.1.10", port=8080)
        assert config.base_url == "http://192.168.1.10:8080"

    def test_load_missing_file(self):
        config = Config.load(Path("/nonexistent/config.toml"))
        assert config.host == "127.0.0.1"
        assert config.port == 11434

    def test_load_from_file(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('host = "10.0.0.1"\nport = 9999\nrefresh_interval = 5.0\n')
        config = Config.load(config_file)
        assert config.host == "10.0.0.1"
        assert config.port == 9999
        assert config.refresh_interval == 5.0

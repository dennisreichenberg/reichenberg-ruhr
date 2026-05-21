from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "ollama-monitor" / "config.toml"


@dataclass
class Config:
    host: str = "127.0.0.1"
    port: int = 11434
    refresh_interval: float = 2.0

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        path = path or DEFAULT_CONFIG_PATH
        if not path.exists():
            return cls()
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls(
            host=data.get("host", cls.host),
            port=data.get("port", cls.port),
            refresh_interval=data.get("refresh_interval", cls.refresh_interval),
        )

from __future__ import annotations

import argparse

from .app import OllamaMonitorApp
from .config import Config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real-time TUI dashboard for Ollama inference"
    )
    parser.add_argument(
        "--host", default=None, help="Ollama host (default: from config or 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Ollama port (default: from config or 11434)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Refresh interval in seconds (default: from config or 2.0)",
    )
    parser.add_argument(
        "--config", default=None, help="Path to config.toml"
    )
    args = parser.parse_args()

    from pathlib import Path

    config = Config.load(Path(args.config) if args.config else None)
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.interval:
        config.refresh_interval = args.interval

    app = OllamaMonitorApp(config=config)
    app.run()


if __name__ == "__main__":
    main()

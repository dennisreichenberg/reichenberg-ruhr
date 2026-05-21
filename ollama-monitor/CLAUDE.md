# ollama-monitor

Real-time TUI dashboard for Ollama inference monitoring.

## Stack

- Python 3.11+
- Textual (TUI framework)
- httpx (async HTTP for Ollama API)
- psutil (system metrics)
- nvidia-smi (GPU metrics, optional)

## Project structure

```
ollama-monitor/
  pyproject.toml
  src/ollama_monitor/
    __init__.py
    __main__.py        # Entry point
    app.py             # Main Textual App
    api.py             # Ollama API client (polling /api/ps, /api/show)
    gpu.py             # GPU/RAM metrics via nvidia-smi + psutil
    config.py          # Config loading from ~/.config/ollama-monitor/config.toml
    widgets/
      __init__.py
      models_table.py     # Running models list widget
      throughput_graph.py  # Live throughput sparkline
      latency_panel.py    # Request queue and latency display
  tests/
    test_api.py
    test_gpu.py
    test_app.py        # Snapshot tests for TUI layout
```

## Commands

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run
ollama-monitor
# or
python -m ollama_monitor

# Tests
pytest

# Lint
ruff check src/ tests/
```

## Keybindings

- `q` -- quit
- `r` -- refresh now
- `p` -- pause/resume auto-refresh

## Config

`~/.config/ollama-monitor/config.toml`:

```toml
host = "127.0.0.1"
port = 11434
refresh_interval = 2.0
```

## Encoding

ASCII-only in strings (`->` not Unicode arrow, `--` not em-dash).
Textual widgets may use Unicode box-drawing (renderer layer).

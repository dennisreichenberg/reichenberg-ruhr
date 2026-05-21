# ollama-monitor

Real-time TUI dashboard for Ollama inference monitoring.

Shows running models, VRAM/RAM usage, throughput, and latencies in a terminal dashboard.

## Install

```bash
pip install ollama-monitor
```

## Usage

```bash
ollama-monitor
ollama-monitor --host 192.168.1.10 --port 11434
ollama-monitor --interval 1.0
```

## Keybindings

- `q` -- quit
- `r` -- refresh now
- `p` -- pause/resume auto-refresh

## Config

Create `~/.config/ollama-monitor/config.toml`:

```toml
host = "127.0.0.1"
port = 11434
refresh_interval = 2.0
```

## Requirements

- Python 3.11+
- Ollama running locally or on a reachable host
- nvidia-smi (optional, for GPU metrics)

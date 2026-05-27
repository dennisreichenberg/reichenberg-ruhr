"""Cloud cost estimation from a configurable YAML price table.

Prices are expressed in USD per 1,000,000 tokens. See ``pricing.yaml`` for the
shipped defaults and the resolution order.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import yaml

_PER_MILLION = 1_000_000


class PricingTable:
    """Resolves (model, backend, tokens) -> estimated USD cost."""

    def __init__(self, data: dict | None = None) -> None:
        data = data or {}
        self._default = _norm_entry(data.get("default"))
        self._backends = {
            str(k).lower(): _norm_entry(v) for k, v in (data.get("backends") or {}).items()
        }
        self._models = {
            str(k).lower(): _norm_entry(v) for k, v in (data.get("models") or {}).items()
        }

    @classmethod
    def load(cls, path: str | Path | None = None) -> "PricingTable":
        """Load a price table from ``path`` or fall back to the packaged one."""
        if path is not None:
            text = Path(path).read_text(encoding="utf-8")
        else:
            text = importlib.resources.files("llm_usage").joinpath("pricing.yaml").read_text(
                encoding="utf-8"
            )
        return cls(yaml.safe_load(text) or {})

    def rate_for(self, model: str, backend: str | None = None) -> tuple[float, float]:
        """Return (input_rate, output_rate) in USD per 1M tokens."""
        model_l = (model or "").lower()
        if model_l in self._models:
            return self._models[model_l]
        # Try the model name with any provider prefix stripped, e.g.
        # "openai/gpt-4o" -> "gpt-4o", "ollama/llama3:8b" -> "llama3:8b".
        if "/" in model_l:
            stripped = model_l.split("/", 1)[1]
            if stripped in self._models:
                return self._models[stripped]
        if backend and backend.lower() in self._backends:
            return self._backends[backend.lower()]
        return self._default

    def estimate(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        backend: str | None = None,
    ) -> float:
        """Estimate the USD cost of a single request."""
        in_rate, out_rate = self.rate_for(model, backend)
        cost = (prompt_tokens * in_rate + completion_tokens * out_rate) / _PER_MILLION
        return round(cost, 6)


def _norm_entry(entry: object) -> tuple[float, float]:
    """Coerce a price entry into an (input, output) float tuple."""
    if entry is None:
        return (0.0, 0.0)
    if isinstance(entry, dict):
        return (float(entry.get("input", 0.0) or 0.0), float(entry.get("output", 0.0) or 0.0))
    # A bare number means the same rate for input and output.
    val = float(entry)
    return (val, val)

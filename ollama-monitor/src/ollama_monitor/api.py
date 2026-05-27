from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from .config import Config


@dataclass
class ModelInfo:
    name: str
    size: int
    vram: int
    expires_at: str
    digest: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def size_gb(self) -> str:
        return f"{self.size / (1024**3):.1f} GB"

    @property
    def vram_gb(self) -> str:
        return f"{self.vram / (1024**3):.1f} GB"


@dataclass
class OllamaStatus:
    models: list[ModelInfo]
    error: str | None = None


class OllamaClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=5.0,
        )

    async def get_running_models(self) -> OllamaStatus:
        try:
            resp = await self._client.get("/api/ps")
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("models", []):
                models.append(
                    ModelInfo(
                        name=m.get("name", "unknown"),
                        size=m.get("size", 0),
                        vram=m.get("size_vram", 0),
                        expires_at=m.get("expires_at", ""),
                        digest=m.get("digest", ""),
                        details=m.get("details", {}),
                    )
                )
            return OllamaStatus(models=models)
        except httpx.HTTPError as exc:
            return OllamaStatus(models=[], error=str(exc))
        except Exception as exc:
            return OllamaStatus(models=[], error=f"Unexpected: {exc}")

    async def close(self) -> None:
        await self._client.aclose()

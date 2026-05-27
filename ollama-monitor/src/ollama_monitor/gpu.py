from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

import psutil


@dataclass
class GpuInfo:
    name: str
    memory_used_mb: int
    memory_total_mb: int
    utilization_pct: int

    @property
    def memory_used_gb(self) -> str:
        return f"{self.memory_used_mb / 1024:.1f}"

    @property
    def memory_total_gb(self) -> str:
        return f"{self.memory_total_mb / 1024:.1f}"


@dataclass
class SystemMetrics:
    gpus: list[GpuInfo]
    ram_used_mb: int
    ram_total_mb: int
    gpu_available: bool

    @property
    def ram_used_gb(self) -> str:
        return f"{self.ram_used_mb / 1024:.1f}"

    @property
    def ram_total_gb(self) -> str:
        return f"{self.ram_total_mb / 1024:.1f}"


def _has_nvidia_smi() -> bool:
    return shutil.which("nvidia-smi") is not None


def _query_nvidia_smi() -> list[GpuInfo]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
        gpus = []
        for line in result.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                gpus.append(
                    GpuInfo(
                        name=parts[0],
                        memory_used_mb=int(parts[1]),
                        memory_total_mb=int(parts[2]),
                        utilization_pct=int(parts[3]),
                    )
                )
        return gpus
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return []


def get_system_metrics() -> SystemMetrics:
    mem = psutil.virtual_memory()
    gpu_available = _has_nvidia_smi()
    gpus = _query_nvidia_smi() if gpu_available else []
    return SystemMetrics(
        gpus=gpus,
        ram_used_mb=int(mem.used / (1024 * 1024)),
        ram_total_mb=int(mem.total / (1024 * 1024)),
        gpu_available=gpu_available,
    )

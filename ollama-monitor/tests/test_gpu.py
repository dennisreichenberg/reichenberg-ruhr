from __future__ import annotations

from unittest.mock import MagicMock, patch

from ollama_monitor.gpu import GpuInfo, SystemMetrics, get_system_metrics

NVIDIA_SMI_OUTPUT = """\
NVIDIA GeForce RTX 4090, 8192, 24576, 45
NVIDIA GeForce RTX 3090, 4096, 24576, 30
"""


class TestGpuInfo:
    def test_memory_format(self):
        gpu = GpuInfo(name="RTX 4090", memory_used_mb=8192, memory_total_mb=24576, utilization_pct=45)
        assert gpu.memory_used_gb == "8.0"
        assert gpu.memory_total_gb == "24.0"


class TestGetSystemMetrics:
    @patch("ollama_monitor.gpu._has_nvidia_smi", return_value=True)
    @patch("ollama_monitor.gpu.subprocess.run")
    @patch("ollama_monitor.gpu.psutil.virtual_memory")
    def test_with_gpu(self, mock_mem, mock_run, mock_has_smi):
        mock_mem.return_value = MagicMock(used=16 * 1024**3, total=64 * 1024**3)
        mock_run.return_value = MagicMock(returncode=0, stdout=NVIDIA_SMI_OUTPUT)

        metrics = get_system_metrics()

        assert metrics.gpu_available is True
        assert len(metrics.gpus) == 2
        assert metrics.gpus[0].name == "NVIDIA GeForce RTX 4090"
        assert metrics.gpus[0].memory_used_mb == 8192
        assert metrics.ram_used_gb == "16.0"

    @patch("ollama_monitor.gpu._has_nvidia_smi", return_value=False)
    @patch("ollama_monitor.gpu.psutil.virtual_memory")
    def test_without_gpu(self, mock_mem, mock_has_smi):
        mock_mem.return_value = MagicMock(used=8 * 1024**3, total=32 * 1024**3)

        metrics = get_system_metrics()

        assert metrics.gpu_available is False
        assert len(metrics.gpus) == 0
        assert metrics.ram_total_gb == "32.0"

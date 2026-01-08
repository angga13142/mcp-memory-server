"""Unit tests for system metrics."""

import asyncio
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.monitoring.metrics.system_metrics import SystemMetrics, system_metrics


class TestSystemMetrics:
    """Test SystemMetrics class."""

    def setup_method(self):
        """Setup for each test."""
        self.metrics = SystemMetrics()
        self.metrics.register()

    def test_register_creates_metrics(self):
        """Test that register creates all metrics."""
        assert self.metrics.memory_usage is not None
        assert self.metrics.cpu_usage is not None
        assert self.metrics.disk_usage is not None
        assert self.metrics.network_bytes_sent is not None
        assert self.metrics.network_bytes_recv is not None

    @patch("src.monitoring.metrics.system_metrics.psutil.virtual_memory")
    def test_collect_memory(self, mock_memory):
        """Test memory collection."""
        # Mock memory data
        mock_memory.return_value = Mock(
            total=8 * 1024 * 1024 * 1024,  # 8GB
            used=4 * 1024 * 1024 * 1024,  # 4GB
            percent=50.0,
        )

        metrics = self.metrics.collect()

        assert "memory_used_bytes" in metrics
        assert metrics["memory_used_bytes"] == 4 * 1024 * 1024 * 1024
        assert metrics["memory_percent"] == 50.0

    @patch("src.monitoring.metrics.system_metrics.psutil.cpu_percent")
    def test_collect_cpu(self, mock_cpu):
        """Test CPU collection."""
        mock_cpu.return_value = 25.5

        metrics = self.metrics.collect()

        assert "cpu_percent" in metrics
        assert metrics["cpu_percent"] == 25.5
        mock_cpu.assert_called_once_with(interval=1)

    @patch("src.monitoring.metrics.system_metrics.psutil.disk_usage")
    def test_collect_disk(self, mock_disk):
        """Test disk collection."""
        mock_disk.return_value = Mock(
            total=100 * 1024 * 1024 * 1024,
            used=50 * 1024 * 1024 * 1024,
            free=50 * 1024 * 1024 * 1024,
            percent=50.0,
        )

        metrics = self.metrics.collect()

        assert "disk_used_bytes" in metrics
        assert metrics["disk_used_bytes"] == 50 * 1024 * 1024 * 1024

    @patch("src.monitoring.metrics.system_metrics.psutil.net_io_counters")
    def test_collect_network(self, mock_net):
        """Test network collection."""
        # First call
        mock_net.return_value = Mock(bytes_sent=1000, bytes_recv=2000)

        metrics1 = self.metrics.collect()

        # Second call (incremental)
        mock_net.return_value = Mock(bytes_sent=1500, bytes_recv=2500)

        metrics2 = self.metrics.collect()

        assert "network_bytes_sent" in metrics2
        assert metrics2["network_bytes_sent"] == 1500

    def test_get_memory_info(self):
        """Test get_memory_info helper."""
        info = self.metrics.get_memory_info()

        assert "total" in info
        assert "used" in info
        assert "free" in info
        assert "percent" in info
        assert info["total"] > 0

    def test_get_cpu_info(self):
        """Test get_cpu_info helper."""
        info = self.metrics.get_cpu_info()

        assert "percent" in info
        assert "count" in info
        assert "load_avg_1m" in info
        assert info["count"] > 0

    def test_get_disk_info(self):
        """Test get_disk_info helper."""
        info = self.metrics.get_disk_info()

        assert "total" in info
        assert "used" in info
        assert "free" in info
        assert "percent" in info
        assert info["total"] > 0

    @patch("src.monitoring.metrics.system_metrics.psutil.virtual_memory")
    def test_collect_handles_errors(self, mock_memory):
        """Test that collect handles errors gracefully."""
        mock_memory.side_effect = Exception("Test error")

        # Should not raise exception
        metrics = self.metrics.collect()

        # Should return empty or partial metrics
        assert isinstance(metrics, dict)


class TestSystemMetricsSingleton:
    """Test system_metrics singleton."""

    def test_singleton_exists(self):
        """Test that singleton instance exists."""
        assert system_metrics is not None

    def test_singleton_is_system_metrics(self):
        """Test that singleton is SystemMetrics instance."""
        assert isinstance(system_metrics, SystemMetrics)

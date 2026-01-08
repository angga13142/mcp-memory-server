"""System-level metrics collection."""

import logging

import psutil
from prometheus_client import Counter, Gauge

from .base import MetricCollector

logger = logging.getLogger(__name__)


class SystemMetrics(MetricCollector):
    """Collect system-level metrics."""

    def __init__(self):
        """Initialize system metrics."""
        self.memory_usage: Gauge = None
        self.cpu_usage: Gauge = None
        self.disk_usage: Gauge = None
        self.network_bytes_sent: Counter = None
        self.network_bytes_recv: Counter = None
        self._last_network_stats = None

    def register(self) -> None:
        """Register system metrics with Prometheus."""
        self.memory_usage = Gauge(
            "mcp_system_memory_usage_bytes", "Memory usage in bytes"
        )

        self.cpu_usage = Gauge(
            "mcp_system_cpu_usage_percent", "CPU usage percentage (0-100)"
        )

        self.disk_usage = Gauge(
            "mcp_system_disk_usage_bytes", "Disk usage in bytes", ["mountpoint"]
        )

        self.network_bytes_sent = Counter(
            "mcp_system_network_bytes_sent_total", "Total bytes sent over network"
        )

        self.network_bytes_recv = Counter(
            "mcp_system_network_bytes_received_total",
            "Total bytes received over network",
        )

        logger.info("System metrics registered")

    def collect(self) -> dict[str, float]:
        """
        Collect current system metrics.

        Returns:
            Dictionary of metric names to values
        """
        metrics = {}

        try:
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            metrics["memory_used_bytes"] = memory.used
            metrics["memory_percent"] = memory.percent

            # CPU usage (averaged over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            metrics["cpu_percent"] = cpu_percent

            # Disk usage
            disk = psutil.disk_usage("/")
            self.disk_usage.labels(mountpoint="/").set(disk.used)
            metrics["disk_used_bytes"] = disk.used

            # Network I/O (incremental)
            net = psutil.net_io_counters()
            if self._last_network_stats:
                bytes_sent = net.bytes_sent - self._last_network_stats.bytes_sent
                bytes_recv = net.bytes_recv - self._last_network_stats.bytes_recv

                if bytes_sent > 0:
                    self.network_bytes_sent.inc(bytes_sent)
                if bytes_recv > 0:
                    self.network_bytes_recv.inc(bytes_recv)

            self._last_network_stats = net
            metrics["network_bytes_sent"] = net.bytes_sent
            metrics["network_bytes_recv"] = net.bytes_recv

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

        return metrics

    def get_memory_info(self) -> dict[str, int]:
        """Get detailed memory information."""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "free": memory.free,
            "percent": memory.percent,
        }

    def get_cpu_info(self) -> dict[str, float]:
        """Get detailed CPU information."""
        return {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "load_avg_1m": psutil.getloadavg()[0],
            "load_avg_5m": psutil.getloadavg()[1],
            "load_avg_15m": psutil.getloadavg()[2],
        }

    def get_disk_info(self) -> dict[str, int]:
        """Get detailed disk information."""
        disk = psutil.disk_usage("/")
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        }


# Singleton instance
system_metrics = SystemMetrics()

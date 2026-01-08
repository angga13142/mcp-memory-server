"""Unit tests for system metrics collector."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.monitoring.collectors import SystemMetricsCollector, system_metrics_collector


class TestSystemMetricsCollector:
    """Test SystemMetricsCollector class."""

    @pytest.mark.asyncio
    async def test_start_collector(self):
        """Test starting collector."""
        collector = SystemMetricsCollector(interval=1)

        # We need to simulate the task manually or cancel it quickly because _collect_loop runs forever
        # But for this unit test, we just want to verify state changes
        # We'll patch _collect_loop to exit immediately

        with patch.object(collector, "_collect_loop", new_callable=AsyncMock):
            await collector.start()

            assert collector._running is True
            assert collector._task is not None

            await collector.stop()

    @pytest.mark.asyncio
    async def test_stop_collector(self):
        """Test stopping collector."""
        collector = SystemMetricsCollector(interval=1)

        # Similar logic, just test state
        with patch.object(collector, "_collect_loop", new_callable=AsyncMock):
            await collector.start()
            await collector.stop()

            assert collector._running is False

    @pytest.mark.asyncio
    async def test_collector_loop_runs(self):
        """Test that collection loop runs."""
        collector = SystemMetricsCollector(interval=0.1)  # Fast interval

        # We start real task but mock metrics
        with patch(
            "src.monitoring.metrics.system_metrics.system_metrics.collect"
        ) as mock_collect:
            mock_collect.return_value = {"cpu_percent": 25.0}

            await collector.start()
            await asyncio.sleep(0.3)  # Wait for a few iterations
            await collector.stop()

            # Should have collected at least once
            assert mock_collect.call_count >= 1

    @pytest.mark.asyncio
    async def test_collector_handles_errors(self):
        """Test that collector handles errors gracefully."""
        collector = SystemMetricsCollector(interval=0.1)

        with patch(
            "src.monitoring.metrics.system_metrics.system_metrics.collect"
        ) as mock_collect:
            mock_collect.side_effect = Exception("Test error")

            await collector.start()
            await asyncio.sleep(0.2)
            await collector.stop()

            # Should not crash, should continue running until stop
            assert collector._running is False  # Stopped now

    @pytest.mark.asyncio
    async def test_cannot_start_twice(self):
        """Test that starting twice doesn't create multiple tasks."""
        collector = SystemMetricsCollector(interval=1)

        with patch.object(collector, "_collect_loop", new_callable=AsyncMock):
            await collector.start()
            first_task = collector._task

            await collector.start()  # Try to start again
            second_task = collector._task

            assert first_task is second_task

            await collector.stop()


class TestSystemMetricsCollectorSingleton:
    """Test system_metrics_collector singleton."""

    def test_singleton_exists(self):
        """Test that singleton exists."""
        assert system_metrics_collector is not None

    def test_singleton_has_default_interval(self):
        """Test singleton has correct default interval."""
        assert system_metrics_collector.interval == 15

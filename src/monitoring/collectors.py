"""Background metric collectors."""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SystemMetricsCollector:
    """Background collector for system metrics."""

    def __init__(self, interval: int = 15):
        """
        Initialize collector.

        Args:
            interval: Collection interval in seconds (default: 15)
        """
        self.interval = interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start background collection."""
        if self._running:
            logger.warning("System metrics collector already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info(f"System metrics collector started (interval: {self.interval}s)")

    async def stop(self) -> None:
        """Stop background collection."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("System metrics collector stopped")

    async def _collect_loop(self) -> None:
        """Background collection loop."""
        from .metrics import system_metrics

        while self._running:
            try:
                # Collect metrics
                metrics = system_metrics.collect()

                logger.debug(
                    f"System metrics collected: "
                    f"CPU={metrics.get('cpu_percent', 0):.1f}%, "
                    f"Memory={metrics.get('memory_percent', 0):.1f}%"
                )

            except Exception as e:
                logger.error(f"Error in system metrics collection: {e}")

            # Wait for next interval
            await asyncio.sleep(self.interval)


# Global instance
system_metrics_collector = SystemMetricsCollector(interval=15)

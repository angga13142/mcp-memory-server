"""Load tests for metrics system."""

import pytest
import asyncio
import time
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.monitoring.metrics import get_metrics, journal_metrics


class TestMetricsPerformance:
    """Test metrics performance under load."""
    
    @pytest.mark.asyncio
    async def test_metrics_overhead(self):
        """Test metrics collection overhead."""
        from src.services.journal_service import JournalService
        from src.storage.database import Database
        from src.storage.vector_store import VectorMemoryStore
        from src.services.search_service import SearchService
        from src.services.memory_service import MemoryService
        from src.utils.config import get_settings
        
        settings = get_settings()
        database = Database(settings)
        await database.init()
        
        vector_store = VectorMemoryStore(settings)
        await vector_store.init()
        
        memory_service = MemoryService(database, vector_store, settings)
        search_service = SearchService(vector_store, database, settings)
        journal_service = JournalService(database, memory_service, search_service, settings)
        
        iterations = 20
        
        start = time.time()
        for i in range(iterations):
            await journal_service.start_work_session(f"Test {i}")
            await journal_service.end_work_session()
        with_metrics = time.time() - start
        
        per_op_time = with_metrics / (iterations * 2)
        
        print(f"\nPer-operation time with metrics: {per_op_time*1000:.2f}ms")
        
        assert per_op_time < 0.1, f"Metrics overhead too high: {per_op_time*1000:.2f}ms"
        
        await database.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_metric_updates(self):
        """Test concurrent metric updates."""
        from src.services.journal_service import JournalService
        from src.storage.database import Database
        from src.storage.vector_store import VectorMemoryStore
        from src.services.search_service import SearchService
        from src.services.memory_service import MemoryService
        from src.utils.config import get_settings
        
        settings = get_settings()
        database = Database(settings)
        await database.init()
        
        vector_store = VectorMemoryStore(settings)
        await vector_store.init()
        
        memory_service = MemoryService(database, vector_store, settings)
        search_service = SearchService(vector_store, database, settings)
        journal_service = JournalService(database, memory_service, search_service, settings)
        
        async def worker(worker_id):
            for i in range(10):
                await journal_service.start_work_session(f"Worker {worker_id} task {i}")
                await asyncio.sleep(0.01)
                await journal_service.end_work_session()
        
        start = time.time()
        await asyncio.gather(*[worker(i) for i in range(5)])
        elapsed = time.time() - start
        
        print(f"\n5 workers, 10 ops each: {elapsed:.2f}s")
        
        assert elapsed < 60, f"Concurrent operations too slow: {elapsed:.2f}s"
        
        await database.close()
    
    def test_metrics_export_performance(self):
        """Test metrics export performance."""
        for i in range(100):
            journal_metrics.sessions_total.labels(status='success').inc()
        
        times = []
        for _ in range(50):
            start = time.time()
            get_metrics()
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        print(f"\nMetrics export avg: {avg_time*1000:.2f}ms")
        print(f"Metrics export p95: {p95_time*1000:.2f}ms")
        
        assert p95_time < 0.1, f"Metrics export too slow: {p95_time*1000:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_metric_cardinality_limit(self):
        """Test system handles metric cardinality well."""
        for i in range(100):
            journal_metrics.sessions_total.labels(status='success').inc()
            journal_metrics.sessions_total.labels(status='failed').inc()
        
        metrics = get_metrics().decode('utf-8')
        
        series_count = metrics.count('mcp_journal_sessions_total{')
        
        print(f"\nTime series for sessions_total: {series_count}")
        
        assert series_count <= 10, f"Too many time series: {series_count}"


class TestMetricsMemoryUsage:
    """Test metrics memory usage."""
    
    @pytest.mark.asyncio
    async def test_memory_growth(self):
        """Test metrics don't cause memory leaks."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not installed")
        
        from src.services.journal_service import JournalService
        from src.storage.database import Database
        from src.storage.vector_store import VectorMemoryStore
        from src.services.search_service import SearchService
        from src.services.memory_service import MemoryService
        from src.utils.config import get_settings
        
        settings = get_settings()
        database = Database(settings)
        await database.init()
        
        vector_store = VectorMemoryStore(settings)
        await vector_store.init()
        
        memory_service = MemoryService(database, vector_store, settings)
        search_service = SearchService(vector_store, database, settings)
        journal_service = JournalService(database, memory_service, search_service, settings)
        
        process = psutil.Process(os.getpid())
        
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        for i in range(100):
            await journal_service.start_work_session(f"Memory test {i}")
            await journal_service.end_work_session()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        memory_growth = final_memory - initial_memory
        
        print(f"\nInitial memory: {initial_memory:.2f}MB")
        print(f"Final memory: {final_memory:.2f}MB")
        print(f"Growth: {memory_growth:.2f}MB")
        
        assert memory_growth < 200, f"Excessive memory growth: {memory_growth:.2f}MB"
        
        await database.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

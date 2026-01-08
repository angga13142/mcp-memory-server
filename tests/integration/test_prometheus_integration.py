"""Integration tests for Prometheus."""

import asyncio
import sys
import time
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPrometheusIntegration:
    """Test integration with Prometheus."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Wait for Prometheus to be ready."""
        max_retries = 30
        for _ in range(max_retries):
            try:
                response = requests.get("http://localhost:9090/-/healthy", timeout=1)
                if response.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            pytest.skip("Prometheus not available")

    def test_prometheus_scrapes_metrics(self):
        """Test Prometheus successfully scrapes metrics."""
        response = requests.get("http://localhost:9090/api/v1/targets")

        assert response.status_code == 200
        data = response.json()

        targets = data["data"]["activeTargets"]
        mcp_target = next(
            (
                t
                for t in targets
                if "mcp-memory-server" in t["labels"].get("job", "")
                or "memory-server" in t["labels"].get("job", "")
            ),
            None,
        )

        assert mcp_target is not None, "MCP target not found"
        assert mcp_target["health"] == "up"

    def test_prometheus_has_journal_metrics(self):
        """Test Prometheus has journal metrics."""
        response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": "mcp_journal_sessions_total"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert len(data["data"]["result"]) > 0

    @pytest.mark.asyncio
    async def test_metrics_appear_in_prometheus(self):
        """Test that new metrics appear in Prometheus."""
        from src.services.journal_service import JournalService
        from src.services.memory_service import MemoryService
        from src.services.search_service import SearchService
        from src.storage.database import Database
        from src.storage.vector_store import VectorMemoryStore
        from src.utils.config import get_settings

        settings = get_settings()
        database = Database(settings)
        await database.init()

        vector_store = VectorMemoryStore(settings)
        await vector_store.init()

        memory_service = MemoryService(database, vector_store, settings)
        search_service = SearchService(vector_store, database, settings)
        journal_service = JournalService(
            database, memory_service, search_service, settings
        )

        await journal_service.start_work_session("Prometheus integration test")
        await asyncio.sleep(2)
        await journal_service.end_work_session()

        await asyncio.sleep(20)

        response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": "mcp_journal_sessions_total"},
        )

        data = response.json()
        assert data["status"] == "success"

        result = data["data"]["result"][0]
        value = float(result["value"][1])
        assert value >= 1

        await database.close()

    def test_prometheus_range_query(self):
        """Test Prometheus range queries work."""
        response = requests.get(
            "http://localhost:9090/api/v1/query_range",
            params={
                "query": "rate(mcp_journal_sessions_total[5m])",
                "start": time.time() - 3600,
                "end": time.time(),
                "step": 60,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_prometheus_histogram_query(self):
        """Test histogram queries work."""
        response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={
                "query": "histogram_quantile(0.95, rate(mcp_journal_session_duration_minutes_bucket[5m]))"
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestPrometheusAlerts:
    """Test Prometheus alerting."""

    def test_alert_rules_loaded(self):
        """Test alert rules are loaded."""
        try:
            response = requests.get("http://localhost:9090/api/v1/rules", timeout=5)
        except requests.exceptions.RequestException:
            pytest.skip("Prometheus not available")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"

        groups = data["data"]["groups"]
        journal_group = next((g for g in groups if g["name"] == "journal_alerts"), None)

        assert journal_group is not None
        assert len(journal_group["rules"]) > 0

    def test_specific_alert_rules_exist(self):
        """Test specific alert rules exist."""
        try:
            response = requests.get("http://localhost:9090/api/v1/rules", timeout=5)
        except requests.exceptions.RequestException:
            pytest.skip("Prometheus not available")

        data = response.json()

        groups = data["data"]["groups"]
        journal_group = next((g for g in groups if g["name"] == "journal_alerts"), None)

        rule_names = [r["name"] for r in journal_group["rules"]]

        expected_rules = [
            "HighSessionFailureRate",
            "ReflectionGenerationFailing",
            "SlowReflectionGeneration",
            "TooManyActiveSessions",
        ]

        for rule in expected_rules:
            assert rule in rule_names, f"Missing alert rule: {rule}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

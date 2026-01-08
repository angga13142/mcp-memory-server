"""Integration tests for Prometheus."""

import time

import pytest
import requests


# Skip all tests if Prometheus is not available
@pytest.mark.integration
class TestPrometheusIntegration:
    """Test Prometheus integration."""

    @pytest.fixture(scope="class")
    def prometheus_url(self):
        """Prometheus URL."""
        return "http://localhost:9090"

    @pytest.fixture(scope="class")
    def app_url(self):
        """Application URL."""
        return "http://localhost:8080"

    @pytest.fixture(scope="class", autouse=True)
    def wait_for_services(self, prometheus_url, app_url):
        """Wait for services to be ready."""
        max_wait = 30
        start_time = time.time()

        # Wait for Prometheus
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{prometheus_url}/-/healthy", timeout=2)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            pytest.skip("Prometheus not available")

        # Wait for application
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{app_url}/health", timeout=2)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            pytest.skip("Application not available")

        # Wait for initial scrape
        time.sleep(15)

    def test_prometheus_is_healthy(self, prometheus_url):
        """Test Prometheus health check."""
        response = requests.get(f"{prometheus_url}/-/healthy")
        assert response.status_code == 200

    def test_prometheus_is_ready(self, prometheus_url):
        """Test Prometheus readiness."""
        response = requests.get(f"{prometheus_url}/-/ready")
        assert response.status_code == 200

    def test_prometheus_targets(self, prometheus_url):
        """Test Prometheus is scraping targets."""
        response = requests.get(f"{prometheus_url}/api/v1/targets")
        data = response.json()

        assert data["status"] == "success"
        assert len(data["data"]["activeTargets"]) > 0

        # Find MCP target
        mcp_target = None
        for target in data["data"]["activeTargets"]:
            if target["labels"].get("job") == "mcp-memory-server":
                mcp_target = target
                break

        assert mcp_target is not None, "MCP target not found"
        assert mcp_target["health"] == "up", f"MCP target is {mcp_target['health']}"

    def test_prometheus_scraping_mcp_metrics(self, prometheus_url):
        """Test Prometheus is collecting MCP metrics."""
        query = "mcp_journal_sessions_total"
        response = requests.get(
            f"{prometheus_url}/api/v1/query", params={"query": query}
        )
        data = response.json()

        assert data["status"] == "success"
        assert len(data["data"]["result"]) > 0, f"No data for metric: {query}"

    def test_prometheus_has_all_journal_metrics(self, prometheus_url):
        """Test Prometheus has all journal metrics."""
        expected_metrics = [
            "mcp_journal_sessions_total",
            "mcp_journal_sessions_active",
            "mcp_journal_session_duration_minutes",
            "mcp_journal_reflections_generated_total",
            "mcp_journal_reflection_generation_seconds",
            "mcp_journal_learnings_captured_total",
            "mcp_journal_challenges_noted_total",
            "mcp_journal_wins_captured_total",
        ]

        for metric in expected_metrics:
            response = requests.get(
                f"{prometheus_url}/api/v1/query", params={"query": metric}
            )
            data = response.json()
            assert data["status"] == "success", f"Query failed for {metric}"

    def test_prometheus_has_database_metrics(self, prometheus_url):
        """Test Prometheus has database metrics."""
        metrics = [
            "mcp_db_connections_active",
            "mcp_db_query_duration_seconds",
            "mcp_db_queries_total",
            "mcp_db_errors_total",
        ]

        for metric in metrics:
            response = requests.get(
                f"{prometheus_url}/api/v1/query", params={"query": metric}
            )
            data = response.json()
            assert data["status"] == "success", f"Failed to query {metric}"

    def test_prometheus_has_system_metrics(self, prometheus_url):
        """Test Prometheus has system metrics."""
        metrics = [
            "mcp_system_memory_usage_bytes",
            "mcp_system_cpu_usage_percent",
            "mcp_system_disk_usage_bytes",
        ]

        for metric in metrics:
            response = requests.get(
                f"{prometheus_url}/api/v1/query", params={"query": metric}
            )
            data = response.json()

            assert data["status"] == "success"
            assert len(data["data"]["result"]) > 0, f"No data for {metric}"

            # Verify value is realistic
            value = float(data["data"]["result"][0]["value"][1])
            if "memory" in metric:
                assert value > 0, f"{metric} should be > 0"
            elif "cpu" in metric:
                assert 0 <= value <= 100, f"{metric} should be 0-100"

    def test_prometheus_alert_rules_loaded(self, prometheus_url):
        """Test alert rules are loaded."""
        response = requests.get(f"{prometheus_url}/api/v1/rules")
        data = response.json()

        assert data["status"] == "success"
        assert len(data["data"]["groups"]) > 0, "No alert rule groups found"

        # Check for journal_alerts group
        group_names = [g["name"] for g in data["data"]["groups"]]
        assert "journal_alerts" in group_names, "journal_alerts group not found"

    def test_prometheus_query_range(self, prometheus_url):
        """Test querying data over time range."""
        end_time = time.time()
        start_time = end_time - 300  # 5 minutes ago

        response = requests.get(
            f"{prometheus_url}/api/v1/query_range",
            params={
                "query": "mcp_system_cpu_usage_percent",
                "start": start_time,
                "end": end_time,
                "step": "15s",
            },
        )
        data = response.json()

        assert data["status"] == "success"
        if len(data["data"]["result"]) > 0:
            values = data["data"]["result"][0]["values"]
            assert len(values) > 0, "No time series data"

    def test_prometheus_metric_metadata(self, prometheus_url):
        """Test metric metadata is available."""
        response = requests.get(
            f"{prometheus_url}/api/v1/metadata",
            params={"metric": "mcp_journal_sessions_total"},
        )
        data = response.json()

        assert data["status"] == "success"
        assert "mcp_journal_sessions_total" in data["data"]

        metadata = data["data"]["mcp_journal_sessions_total"][0]
        assert "type" in metadata
        assert "help" in metadata

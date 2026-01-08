"""Full stack integration tests."""

import time

import pytest
import requests


@pytest.mark.integration
class TestFullStackIntegration:
    """Test full stack integration."""

    @pytest.fixture(scope="class")
    def all_services(self):
        """Ensure all services are running."""
        services = {
            "app": "http://localhost:8080/health",
            "prometheus": "http://localhost:9090/-/healthy",
            "grafana": "http://localhost:3000/api/health",
        }

        max_wait = 60
        for name, url in services.items():
            start = time.time()
            while time.time() - start < max_wait:
                try:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        break
                except requests.exceptions.RequestException:
                    time.sleep(2)
            else:
                pytest.skip(f"{name} service not available")

        # Wait for metrics collection
        time.sleep(15)

        return services

    def test_full_monitoring_pipeline(self, all_services):
        """Test complete monitoring pipeline."""
        # 1. Generate activity in application
        response = requests.get("http://localhost:8080/metrics")
        assert response.status_code == 200

        # 2. Verify Prometheus scraped the metrics
        time.sleep(15)  # Wait for scrape

        prom_response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": 'up{job="mcp-memory-server"}'},
        )
        prom_data = prom_response.json()

        assert prom_data["status"] == "success"
        assert len(prom_data["data"]["result"]) > 0

        # 3. Verify Grafana can query Prometheus
        grafana_response = requests.get(
            "http://localhost:3000/api/datasources/proxy/1/api/v1/query",
            params={"query": "up"},
            auth=("admin", "admin"),
        )

        assert grafana_response.status_code == 200

    def test_metrics_to_dashboard_flow(self, all_services):
        """Test metrics flow from app to dashboard."""
        # 1. Check application exposes metrics
        app_metrics = requests.get("http://localhost:8080/metrics").text
        assert "mcp_system_memory_usage_bytes" in app_metrics

        # 2. Check Prometheus has the metric
        time.sleep(15)
        prom_response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": "mcp_system_memory_usage_bytes"},
        )
        prom_data = prom_response.json()
        assert len(prom_data["data"]["result"]) > 0

        # 3. Check Grafana can query it
        grafana_response = requests.get(
            "http://localhost:3000/api/datasources/proxy/1/api/v1/query",
            params={"query": "mcp_system_memory_usage_bytes"},
            auth=("admin", "admin"),
        )
        grafana_data = grafana_response.json()
        assert grafana_data["status"] == "success"

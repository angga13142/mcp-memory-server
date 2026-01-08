"""Integration tests for Grafana."""

import time

import pytest
import requests


@pytest.mark.skipif(True, reason="Requires running Grafana on port 3000")
class TestGrafanaIntegration:
    """Test integration with Grafana."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup Grafana connection."""
        max_retries = 30
        for _ in range(max_retries):
            try:
                response = requests.get("http://localhost:3000/api/health", timeout=1)
                if response.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            pytest.skip("Grafana not available")

        self.auth = ("admin", "admin")

    def test_grafana_health(self):
        """Test Grafana is healthy."""
        response = requests.get("http://localhost:3000/api/health", auth=self.auth)

        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "ok"

    def test_prometheus_datasource_configured(self):
        """Test Prometheus datasource is configured."""
        response = requests.get("http://localhost:3000/api/datasources", auth=self.auth)

        assert response.status_code == 200
        datasources = response.json()

        prometheus_ds = next(
            (ds for ds in datasources if ds["type"] == "prometheus"), None
        )

        assert prometheus_ds is not None
        assert prometheus_ds["url"] == "http://prometheus:9090"

    def test_datasource_connection(self):
        """Test datasource connection works."""
        response = requests.get("http://localhost:3000/api/datasources", auth=self.auth)
        datasources = response.json()
        prometheus_ds = next(ds for ds in datasources if ds["type"] == "prometheus")

        response = requests.get(
            f"http://localhost:3000/api/datasources/{prometheus_ds['id']}/health",
            auth=self.auth,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"

    def test_dashboard_exists(self):
        """Test MCP dashboard exists."""
        response = requests.get(
            "http://localhost:3000/api/search",
            params={"query": "MCP Memory Server"},
            auth=self.auth,
        )

        assert response.status_code == 200
        dashboards = response.json()

        assert len(dashboards) > 0
        assert any("journal" in d["title"].lower() for d in dashboards)

    def test_dashboard_loads(self):
        """Test dashboard loads without errors."""
        response = requests.get(
            "http://localhost:3000/api/search",
            params={"query": "MCP Memory Server"},
            auth=self.auth,
        )
        dashboards = response.json()

        if not dashboards:
            pytest.skip("No dashboards found")

        dashboard = dashboards[0]

        response = requests.get(
            f"http://localhost:3000/api/dashboards/uid/{dashboard['uid']}",
            auth=self.auth,
        )

        assert response.status_code == 200
        data = response.json()

        assert "dashboard" in data
        assert len(data["dashboard"]["panels"]) > 0

    def test_dashboard_panels_have_queries(self):
        """Test dashboard panels have valid queries."""
        response = requests.get(
            "http://localhost:3000/api/search",
            params={"query": "MCP Memory Server"},
            auth=self.auth,
        )
        dashboards = response.json()

        if not dashboards:
            pytest.skip("No dashboards found")

        dashboard = dashboards[0]

        response = requests.get(
            f"http://localhost:3000/api/dashboards/uid/{dashboard['uid']}",
            auth=self.auth,
        )
        data = response.json()

        panels = data["dashboard"]["panels"]

        panels_with_queries = [
            p for p in panels if p.get("type") not in ["row"] and p.get("targets")
        ]

        assert len(panels_with_queries) > 0

        for panel in panels_with_queries:
            for target in panel["targets"]:
                assert target.get("expr"), f"Panel {panel.get('title')} has empty query"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

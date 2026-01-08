"""Integration tests for Grafana."""

import time

import pytest
import requests


@pytest.mark.integration
class TestGrafanaIntegration:
    """Test Grafana integration."""

    @pytest.fixture(scope="class")
    def grafana_url(self):
        """Grafana URL."""
        return "http://localhost:3000"

    @pytest.fixture(scope="class")
    def grafana_auth(self):
        """Grafana authentication."""
        return ("admin", "admin")

    @pytest.fixture(scope="class", autouse=True)
    def wait_for_grafana(self, grafana_url):
        """Wait for Grafana to be ready."""
        max_wait = 60
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{grafana_url}/api/health", timeout=2)
                if response.status_code == 200:
                    time.sleep(5)  # Additional wait for full initialization
                    return
            except requests.exceptions.RequestException:
                time.sleep(2)

        pytest.skip("Grafana not available")

    def test_grafana_health(self, grafana_url):
        """Test Grafana health endpoint."""
        response = requests.get(f"{grafana_url}/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "ok"

    def test_grafana_login(self, grafana_url, grafana_auth):
        """Test Grafana authentication."""
        response = requests.get(f"{grafana_url}/api/org", auth=grafana_auth)

        assert response.status_code == 200
        data = response.json()
        assert "name" in data

    def test_grafana_datasources_exist(self, grafana_url, grafana_auth):
        """Test Prometheus datasource exists."""
        response = requests.get(f"{grafana_url}/api/datasources", auth=grafana_auth)

        assert response.status_code == 200
        datasources = response.json()

        assert len(datasources) > 0, "No datasources found"

        # Check for Prometheus datasource
        prometheus_ds = None
        for ds in datasources:
            if ds["type"] == "prometheus":
                prometheus_ds = ds
                break

        assert prometheus_ds is not None, "Prometheus datasource not found"
        assert prometheus_ds["url"] == "http://prometheus:9090"
        assert prometheus_ds["isDefault"] is True

    def test_grafana_datasource_health(self, grafana_url, grafana_auth):
        """Test Prometheus datasource is healthy."""
        # Get datasource
        response = requests.get(f"{grafana_url}/api/datasources", auth=grafana_auth)
        datasources = response.json()

        prometheus_ds = next(
            (ds for ds in datasources if ds["type"] == "prometheus"), None
        )

        assert prometheus_ds is not None

        # Test datasource
        response = requests.get(
            f"{grafana_url}/api/datasources/{prometheus_ds['id']}/health",
            auth=grafana_auth,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK" or "success" in data.get("message", "").lower()

    def test_grafana_dashboards_exist(self, grafana_url, grafana_auth):
        """Test dashboards are provisioned."""
        response = requests.get(
            f"{grafana_url}/api/search?type=dash-db", auth=grafana_auth
        )

        assert response.status_code == 200
        dashboards = response.json()

        assert (
            len(dashboards) >= 2
        ), f"Expected at least 2 dashboards, found {len(dashboards)}"

    def test_grafana_journal_dashboard(self, grafana_url, grafana_auth):
        """Test Journal Overview dashboard."""
        # Search for dashboard
        response = requests.get(
            f"{grafana_url}/api/search?query=journal", auth=grafana_auth
        )

        dashboards = response.json()

        if len(dashboards) == 0:
            pytest.skip("Journal dashboard not found - may need manual provisioning")

        dashboard = dashboards[0]

        # Get dashboard details
        response = requests.get(
            f"{grafana_url}/api/dashboards/uid/{dashboard['uid']}", auth=grafana_auth
        )

        assert response.status_code == 200
        data = response.json()

        assert "dashboard" in data
        assert data["dashboard"]["title"]
        assert len(data["dashboard"]["panels"]) > 0, "Dashboard has no panels"

    def test_grafana_performance_dashboard(self, grafana_url, grafana_auth):
        """Test Performance dashboard."""
        response = requests.get(
            f"{grafana_url}/api/search?query=performance", auth=grafana_auth
        )

        dashboards = response.json()

        if len(dashboards) == 0:
            pytest.skip("Performance dashboard not found")

        dashboard = dashboards[0]

        # Get dashboard details
        response = requests.get(
            f"{grafana_url}/api/dashboards/uid/{dashboard['uid']}", auth=grafana_auth
        )

        assert response.status_code == 200
        data = response.json()

        panels = data["dashboard"]["panels"]
        assert len(panels) >= 5, f"Expected at least 5 panels, found {len(panels)}"

    def test_grafana_panel_data_query(self, grafana_url, grafana_auth):
        """Test querying data for a dashboard panel."""
        # Get first dashboard
        response = requests.get(
            f"{grafana_url}/api/search?type=dash-db", auth=grafana_auth
        )
        dashboards = response.json()

        if len(dashboards) == 0:
            pytest.skip("No dashboards available")

        dashboard = dashboards[0]

        # Get dashboard details
        response = requests.get(
            f"{grafana_url}/api/dashboards/uid/{dashboard['uid']}", auth=grafana_auth
        )
        dashboard_data = response.json()

        # Get first panel with targets
        panel = None
        for p in dashboard_data["dashboard"]["panels"]:
            if "targets" in p and len(p["targets"]) > 0:
                panel = p
                break

        if panel is None:
            pytest.skip("No panels with queries found")

        # Verify panel has query
        assert len(panel["targets"]) > 0
        assert "expr" in panel["targets"][0]

    def test_grafana_alert_rules(self, grafana_url, grafana_auth):
        """Test alert rules in Grafana (if configured)."""
        response = requests.get(
            f"{grafana_url}/api/ruler/grafana/api/v1/rules", auth=grafana_auth
        )

        # Alert rules are optional in Grafana
        assert response.status_code in [200, 404]

    def test_grafana_folders(self, grafana_url, grafana_auth):
        """Test dashboard folders exist."""
        response = requests.get(f"{grafana_url}/api/folders", auth=grafana_auth)

        assert response.status_code == 200
        # Folders are optional but endpoint should work

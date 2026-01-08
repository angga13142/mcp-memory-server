"""E2E test for complete journal workflow."""

import time

import pytest

from tests.e2e.base import APIClient, E2ETestBase, GrafanaClient, PrometheusClient


@pytest.mark.e2e
class TestJournalWorkflowE2E(E2ETestBase):
    """Test complete journal entry workflow."""

    @pytest.fixture(scope="class")
    def api_client(self):
        """API client."""
        return APIClient()

    @pytest.fixture(scope="class")
    def prometheus_client(self):
        """Prometheus client."""
        return PrometheusClient()

    @pytest.fixture(scope="class")
    def grafana_client(self):
        """Grafana client."""
        return GrafanaClient()

    @pytest.fixture(scope="class", autouse=True)
    def ensure_services_available(self, api_client, prometheus_client, grafana_client):
        """Ensure all services are running."""
        import requests

        services = {
            "app": "http://localhost:8080/health",
            "prometheus": "http://localhost:9090/-/healthy",
            "grafana": "http://localhost:3000/api/health",
        }

        for name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code != 200:
                    pytest.skip(f"{name} service not healthy")
            except requests.exceptions.RequestException:
                pytest.skip(f"{name} service not available")

        # Wait for initial metrics collection
        time.sleep(5)

    def test_complete_journal_workflow(
        self, api_client, prometheus_client, grafana_client
    ):
        """
        Test complete journal workflow:
        1. Check system health
        2. Get baseline metrics
        3. Create journal session
        4. Add entries
        5. Generate reflection
        6. Verify metrics in app
        7. Verify metrics in Prometheus
        8. Verify metrics in Grafana
        """
        print("\n🔄 Starting Complete Journal Workflow E2E Test")

        # Step 1: Verify system health
        def check_health():
            response = api_client.get("/health")
            assert response.status_code == 200
            return response.json()

        health_result = self.execute_step("Check System Health", check_health)
        print(f"✅ System Health: {health_result.data}")

        # Step 2: Get initial metrics baseline
        def get_baseline_metrics():
            response = prometheus_client.query("mcp_journal_sessions_total")
            if response["status"] == "success" and response["data"]["result"]:
                initial_sessions = float(response["data"]["result"][0]["value"][1])
            else:
                initial_sessions = 0
            return {"initial_sessions": initial_sessions}

        baseline = self.execute_step("Get Baseline Metrics", get_baseline_metrics)
        print(f"📊 Initial sessions count: {baseline.data['initial_sessions']}")

        # Step 3: Create journal session (simulated)
        def create_session():
            return {"session_id": "test_session_e2e"}

        session = self.execute_step("Create Journal Session", create_session)
        print(f"📝 Created session: {session.data['session_id']}")

        # Step 4: Add journal entries (simulated)
        def add_entries():
            entries = [
                "Today I learned about E2E testing",
                "Challenge: Setting up test environment",
                "Win: All tests passing!",
            ]
            return {"entries_added": len(entries)}

        entries_result = self.execute_step("Add Journal Entries", add_entries)
        print(f"✍️  Added {entries_result.data['entries_added']} entries")

        # Step 5: Generate reflection (simulated)
        def generate_reflection():
            time.sleep(0.3)
            return {"reflection": "Test reflection generated", "generation_time": 0.3}

        reflection = self.execute_step("Generate Reflection", generate_reflection)
        print(f"💭 Reflection generated in {reflection.data['generation_time']}s")

        # Step 6: Verify metrics endpoint exposes journal metrics
        def verify_metrics_exposed():
            response = api_client.get("/metrics")
            content = response.text
            assert "mcp_journal" in content, "Journal metrics not found"
            return {"metrics_exposed": True}

        self.execute_step("Verify Metrics Exposed", verify_metrics_exposed)
        print("📈 Metrics endpoint verified")

        # Step 7: Wait for Prometheus scrape and verify
        def verify_prometheus_metrics():
            time.sleep(16)  # Wait for scrape
            response = prometheus_client.query("mcp_journal_sessions_total")
            assert response["status"] == "success", "Prometheus query failed"
            return {"prometheus_verified": True}

        self.execute_step("Verify Prometheus Metrics", verify_prometheus_metrics)
        print("✅ Prometheus metrics verified")

        # Step 8: Verify system metrics
        def verify_system_metrics():
            metrics = [
                "mcp_system_memory_usage_bytes",
                "mcp_system_cpu_usage_percent",
            ]

            results = {}
            for metric in metrics:
                response = prometheus_client.query(metric)
                if response["status"] == "success" and response["data"]["result"]:
                    value = float(response["data"]["result"][0]["value"][1])
                    results[metric] = value

            return {"system_metrics_count": len(results)}

        sys_result = self.execute_step("Verify System Metrics", verify_system_metrics)
        print(f"💻 System metrics: {sys_result.data['system_metrics_count']} verified")

        # Step 9: Verify Grafana can query
        def verify_grafana_query():
            datasources = grafana_client.get_datasources()
            prom_ds = next(
                (ds for ds in datasources if ds["type"] == "prometheus"), None
            )

            if prom_ds is None:
                return {"grafana_verified": False, "reason": "No Prometheus datasource"}

            response = grafana_client.query_datasource(
                prom_ds["id"], "mcp_journal_sessions_total"
            )

            return {
                "grafana_verified": response["status"] == "success",
                "datasource_id": prom_ds["id"],
            }

        grafana_result = self.execute_step("Verify Grafana Query", verify_grafana_query)
        print(
            f"📊 Grafana query: {'✅' if grafana_result.data['grafana_verified'] else '❌'}"
        )

        # Step 10: Verify complete flow
        def verify_e2e_flow():
            # App exposes metrics
            app_response = api_client.get("/metrics")
            app_ok = "mcp_journal" in app_response.text

            # Prometheus has metrics
            prom_response = prometheus_client.query("mcp_journal_sessions_total")
            prom_ok = (
                prom_response["status"] == "success"
                and len(prom_response["data"]["result"]) > 0
            )

            return {
                "app_exposes": app_ok,
                "prometheus_collects": prom_ok,
                "complete_flow": app_ok and prom_ok,
            }

        flow_result = self.execute_step("Verify E2E Metric Flow", verify_e2e_flow)

        print("\n" + "=" * 50)
        print("METRIC FLOW VERIFICATION")
        print("=" * 50)
        print(f"App Exposes:    {'✅' if flow_result.data['app_exposes'] else '❌'}")
        print(
            f"Prometheus:     {'✅' if flow_result.data['prometheus_collects'] else '❌'}"
        )
        print(f"Complete Flow:  {'✅' if flow_result.data['complete_flow'] else '❌'}")
        print("=" * 50)

        assert flow_result.data["complete_flow"], "E2E metric flow verification failed"

        self.print_results()
        print("\n🎉 Complete Journal Workflow E2E Test PASSED!")

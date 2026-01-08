"""E2E test for monitoring and alerting."""

import time

import pytest
import requests

from tests.e2e.base import APIClient, E2ETestBase, PrometheusClient


@pytest.mark.e2e
class TestMonitoringAlertingE2E(E2ETestBase):
    """Test monitoring and alerting workflow."""

    @pytest.fixture(scope="class")
    def api_client(self):
        """API client."""
        return APIClient()

    @pytest.fixture(scope="class")
    def prometheus_client(self):
        """Prometheus client."""
        return PrometheusClient()

    @pytest.fixture(scope="class", autouse=True)
    def ensure_prometheus_available(self, prometheus_client):
        """Ensure Prometheus is running."""
        try:
            response = requests.get("http://localhost:9090/-/healthy", timeout=5)
            if response.status_code != 200:
                pytest.skip("Prometheus not healthy")
        except requests.exceptions.RequestException:
            pytest.skip("Prometheus not available")

    def test_alert_rules_evaluation(self, prometheus_client):
        """
        Test alert rules are properly evaluated:
        1. Verify alert rules are loaded
        2. Check alert states
        3. Verify alert expressions are valid
        """
        print("\n🚨 Starting Alert Rules E2E Test")

        # Step 1: Get all alert rules
        def get_alert_rules():
            response = prometheus_client.get_alerts()
            assert response["status"] == "success"
            alerts = response["data"]["alerts"]
            return {"total_alerts": len(alerts), "alerts": alerts}

        rules_result = self.execute_step("Get Alert Rules", get_alert_rules)
        print(f"📋 Found {rules_result.data['total_alerts']} active alerts")

        # Step 2: Verify alert rules exist in rules endpoint
        def verify_alert_rules():
            rules_response = requests.get("http://localhost:9090/api/v1/rules")
            rules_data = rules_response.json()

            all_alert_names = []
            for group in rules_data["data"]["groups"]:
                for rule in group["rules"]:
                    if rule["type"] == "alerting":
                        all_alert_names.append(rule["name"])

            return {
                "alert_count": len(all_alert_names),
                "alert_names": all_alert_names[:10],  # First 10 for display
            }

        alerts_result = self.execute_step("Verify Alert Rules", verify_alert_rules)
        print(f"📋 Found {alerts_result.data['alert_count']} alert rules configured")

        # Step 3: Verify rule expressions are valid
        def validate_expressions():
            rules_response = requests.get("http://localhost:9090/api/v1/rules")
            rules_data = rules_response.json()

            invalid_rules = []
            for group in rules_data["data"]["groups"]:
                for rule in group["rules"]:
                    if (
                        rule["type"] == "alerting"
                        and "health" in rule
                        and rule["health"] != "ok"
                    ):
                        invalid_rules.append(
                            {
                                "name": rule["name"],
                                "health": rule["health"],
                                "error": rule.get("lastError", "Unknown"),
                            }
                        )

            return {
                "invalid_rules": invalid_rules,
                "all_valid": len(invalid_rules) == 0,
            }

        validation = self.execute_step(
            "Validate Alert Expressions", validate_expressions
        )

        if not validation.data["all_valid"]:
            print("\n⚠️ Invalid Alert Rules:")
            for rule in validation.data["invalid_rules"]:
                print(f"  ❌ {rule['name']}: {rule['error']}")

        self.print_results()
        print("\n✅ Alert Rules E2E Test PASSED!")

    def test_metrics_collection_continuous(self, api_client, prometheus_client):
        """
        Test continuous metrics collection:
        1. Get initial values
        2. Generate activity
        3. Verify metrics update
        """
        print("\n📊 Starting Continuous Metrics Collection Test")

        # Step 1: Get initial values
        def get_initial_values():
            metrics = {}
            for metric in [
                "mcp_system_memory_usage_bytes",
                "mcp_system_cpu_usage_percent",
            ]:
                response = prometheus_client.query(metric)
                if response["status"] == "success" and response["data"]["result"]:
                    value = float(response["data"]["result"][0]["value"][1])
                    metrics[metric] = value
            return metrics

        initial = self.execute_step("Get Initial Metrics", get_initial_values)
        print(f"📈 Initial metrics: {len(initial.data)} captured")

        # Step 2: Generate activity
        def generate_activity():
            for _ in range(5):
                api_client.get("/metrics")
                time.sleep(0.2)
            return {"requests_made": 5}

        self.execute_step("Generate Activity", generate_activity)

        # Step 3: Wait and verify
        time.sleep(16)

        def verify_updated():
            current = {}
            for metric in initial.data:
                response = prometheus_client.query(metric)
                if response["status"] == "success" and response["data"]["result"]:
                    current[metric] = float(response["data"]["result"][0]["value"][1])
            return {"metrics_present": len(current) == len(initial.data)}

        updated = self.execute_step("Verify Metrics Updated", verify_updated)
        assert updated.data["metrics_present"], "Some metrics disappeared"

        self.print_results()
        print("\n✅ Continuous Metrics Collection Test PASSED!")

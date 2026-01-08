"""Test alert triggering scenarios."""

import asyncio
import sys
import time
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestAlertScenarios:
    """Test various alert scenarios."""

    @pytest.fixture(autouse=True)
    def wait_for_prometheus(self):
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

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_too_many_active_sessions_alert(self):
        """Test TooManyActiveSessions alert triggers."""
        from src.services.journal_service import JournalService
        from src.services.memory_service import MemoryService
        from src.services.search_service import SearchService
        from src.storage.database import Database
        from src.storage.vector_store import VectorMemoryStore
        from src.utils.config import get_settings

        print("\n🧪 Testing TooManyActiveSessions alert...")

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

        session_ids = []
        for i in range(12):
            result = await journal_service.start_work_session(f"Alert test session {i}")
            session_ids.append(result["session_id"])
            await asyncio.sleep(1)

        print(f"Started {len(session_ids)} sessions")

        print("Waiting 16 minutes for alert to fire...")
        await asyncio.sleep(960)

        response = requests.get("http://localhost:9090/api/v1/alerts")
        data = response.json()

        alerts = data["data"]["alerts"]
        active_alert = next(
            (a for a in alerts if a["labels"]["alertname"] == "TooManyActiveSessions"),
            None,
        )

        assert active_alert is not None, "Alert did not fire"
        assert active_alert["state"] == "firing"

        print("✅ Alert fired successfully")

        for _ in range(12):
            await journal_service.end_work_session()

        await asyncio.sleep(300)

        response = requests.get("http://localhost:9090/api/v1/alerts")
        data = response.json()
        alerts = data["data"]["alerts"]

        resolved = all(
            a["labels"]["alertname"] != "TooManyActiveSessions"
            or a["state"] != "firing"
            for a in alerts
        )

        assert resolved, "Alert did not resolve after cleanup"
        print("✅ Alert resolved successfully")

        await database.close()

    @pytest.mark.asyncio
    async def test_high_session_failure_rate_alert(self):
        """Test HighSessionFailureRate alert."""
        print("\n🧪 Testing HighSessionFailureRate alert...")

        response = requests.get("http://localhost:9090/api/v1/rules")
        data = response.json()

        groups = data["data"]["groups"]
        journal_group = next(g for g in groups if g["name"] == "journal_alerts")

        alert_rule = next(
            (
                r
                for r in journal_group["rules"]
                if r["name"] == "HighSessionFailureRate"
            ),
            None,
        )

        assert alert_rule is not None
        assert alert_rule["type"] == "alerting"

        print("✅ Alert rule configured correctly")

    def test_alert_annotations(self):
        """Test alerts have proper annotations."""
        response = requests.get("http://localhost:9090/api/v1/rules")
        data = response.json()

        groups = data["data"]["groups"]
        journal_group = next(g for g in groups if g["name"] == "journal_alerts")

        for rule in journal_group["rules"]:
            if rule["type"] == "alerting":
                assert "annotations" in rule
                assert "summary" in rule["annotations"]
                assert "description" in rule["annotations"]

                print(f"✅ {rule['name']}: Has proper annotations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])

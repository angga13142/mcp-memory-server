"""End-to-end user scenarios for Daily Work Journal."""

import asyncio
from pathlib import Path

import pytest

from src.server import (
    capture_win,
)
from src.server import cleanup as server_cleanup
from src.server import (
    end_work_session,
    get_services,
    how_was_my_day,
    morning_briefing_prompt,
    set_morning_intention,
    start_working_on,
)
from src.utils.config import get_settings


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_e2e_environment():
    """Setup E2E test environment."""
    settings = get_settings()

    # Use separate E2E test paths
    test_db_path = Path("data/test_e2e_memory.db")
    test_chroma_path = Path("data/test_e2e_chroma")

    settings.storage.sqlite.database_url = f"sqlite+aiosqlite:///{test_db_path}"
    settings.storage.chroma.persist_directory = str(test_chroma_path)

    # Clean up before
    if test_db_path.exists():
        test_db_path.unlink()
    if test_chroma_path.exists():
        import shutil

        shutil.rmtree(test_chroma_path)

    # Initialize services
    await get_services()

    yield

    # Cleanup after
    await server_cleanup()

    if test_db_path.exists():
        test_db_path.unlink()
    if test_chroma_path.exists():
        import shutil

        shutil.rmtree(test_chroma_path)


@pytest.mark.asyncio
class TestUserScenarios:
    """E2E User Scenarios."""

    async def test_productive_developer_day(self):
        """Scenario: A developer having a productive day with multiple sessions."""

        # 1. Morning Routine
        briefing = await morning_briefing_prompt.fn()
        assert "Morning Briefing" in briefing

        await set_morning_intention.fn(
            intention="Refactor authentication system and fix critical bugs"
        )

        # 2. Session 1: Deep Work (90 mins)
        await start_working_on.fn(task="Auth System Refactoring")

        # Simulate time passing (fast-forward) via direct DB manipulation if needed,
        # but here we just rely on logic functioning.
        # To test specific duration logic, we might need to mock datetime,
        # but for E2E flow, we just verify the sequence.

        await end_work_session.fn(
            what_i_learned=["OAuth2 flow is complex", "Need better error handling"],
            quick_note="Completed the login handler.",
        )

        # 3. Quick Win
        await capture_win.fn(win="Fixed the infinite redirect bug!")

        # 4. Session 2: Bug Fixing (45 mins)
        await start_working_on.fn(task="Fixing reported bugs")
        await end_work_session.fn(challenges_faced=["Reproduction steps were unclear"])

        # 5. End of Day
        summary = await how_was_my_day.fn()
        assert summary["success"] is True
        assert "Auth System Refactoring" in summary["summary"]
        assert summary["stats"]["sessions"] == 2
        assert summary["stats"]["learnings_captured"] >= 2

    async def test_struggling_day_recovery(self):
        """Scenario: A day starting with blockers but recovering."""

        # 1. Start with a challenge
        await start_working_on.fn(task="Debugging legacy code")

        await end_work_session.fn(
            challenges_faced=["Code is undocumented", "Tests are failing"],
            quick_note="Made zero progress. Frustrated.",
        )

        # 2. Reset Intention
        await set_morning_intention.fn(intention="Just focus on one small module")

        # 3. Small win
        await start_working_on.fn(task="Documenting one module")
        await end_work_session.fn(
            what_i_learned=["Module X handles payments"],
            quick_note="At least I understand it now.",
        )

        await capture_win.fn(win="Documented the payment module")

        # 4. Summary
        summary = await how_was_my_day.fn()
        assert summary["success"] is True
        # Summary should acknowledge challenges but also the win
        assert "Debugging legacy code" in summary["summary"]

    async def test_interrupted_workflow(self):
        """Scenario: Forgot to end session, started new one."""

        # 1. Start session
        await start_working_on.fn(task="Initial task")

        # 2. Try to start another without ending (Simulate interruption/forgetfulness)
        # The system currently blocks this, prompting user to end.
        result = await start_working_on.fn(task="New urgent task")
        assert result["success"] is False
        assert "already active" in result["error"]

        # 3. User realizes and ends previous
        await end_work_session.fn(quick_note="Got interrupted")

        # 4. Starts new one
        await start_working_on.fn(task="New urgent task")
        await end_work_session.fn()

        # Verify both recorded
        summary = await how_was_my_day.fn()
        assert summary["stats"]["sessions"] >= 2

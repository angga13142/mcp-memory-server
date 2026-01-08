"""Integration tests for MCP tools with real services."""

import pytest
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from src.server import (
    start_working_on,
    end_work_session,
    how_was_my_day,
    set_morning_intention,
    capture_win,
    morning_briefing_prompt,
    active_session_prompt,
    daily_progress_prompt,
    get_services,
    cleanup as server_cleanup
)
from src.utils.config import get_settings


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_test_environment():
    """Setup test environment."""
    settings = get_settings()
    
    # Use test paths
    test_db_path = Path("data/test_mcp_memory.db")
    test_chroma_path = Path("data/test_mcp_chroma")
    
    settings.storage.sqlite.database_url = f"sqlite+aiosqlite:///{test_db_path}"
    settings.storage.chroma.persist_directory = str(test_chroma_path)
    
    # Clean up
    if test_db_path.exists():
        test_db_path.unlink()
    if test_chroma_path.exists():
        import shutil
        shutil.rmtree(test_chroma_path)
    
    # Initialize services
    await get_services()
    
    yield
    
    # Cleanup
    await server_cleanup()
    
    if test_db_path.exists():
        test_db_path.unlink()
    if test_chroma_path.exists():
        import shutil
        shutil.rmtree(test_chroma_path)


@pytest.mark.asyncio
class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""
    
    async def test_complete_workday_flow(self):
        """Test complete workday using MCP tools."""
        # Morning: Set intention
        # Use .fn(intention="...") to bypass the Tool object wrapper
        intention_result = await set_morning_intention.fn(
            intention="Complete MCP integration tests"
        )
        assert intention_result["success"] is True
        
        # Morning: Check briefing
        briefing = await morning_briefing_prompt.fn()
        assert len(briefing) > 0
        assert "briefing" in briefing.lower() or "morning" in briefing.lower()
        
        # Work session 1
        start_result = await start_working_on.fn(task="Writing integration tests")
        assert start_result["success"] is True
        session1_id = start_result["session_id"]
        
        # Check active session
        active_status = await active_session_prompt.fn()
        assert "writing integration tests" in active_status.lower()
        
        # Capture a win
        win_result = await capture_win.fn(win="All integration tests passing!")
        assert win_result["success"] is True
        
        # Wait and end session
        await asyncio.sleep(2)
        end_result = await end_work_session.fn(
            what_i_learned=["MCP tools work seamlessly together"],
            quick_note="Great progress on testing"
        )
        assert end_result["success"] is True
        assert end_result["session_id"] == session1_id
        
        # Check progress
        progress = await daily_progress_prompt.fn()
        assert "1" in progress or "completed" in progress.lower()
        
        # Work session 2
        await start_working_on.fn(task="Documenting test patterns")
        await asyncio.sleep(1)
        await end_work_session.fn(
            what_i_learned=["Documentation is crucial"]
        )
        
        # Evening: Get daily summary
        summary_result = await how_was_my_day.fn()
        assert summary_result["success"] is True
        assert summary_result["stats"]["sessions"] >= 2
        assert summary_result["stats"]["learnings_captured"] >= 2
    
    async def test_error_handling_in_mcp_tools(self):
        """Test error handling across MCP tools."""
        # Try to start with empty task
        result = await start_working_on.fn(task="")
        assert result["success"] is False
        assert "required" in result["error"].lower()
        
        # Try to end without active session
        result = await end_work_session.fn()
        assert result["success"] is False
        assert "no active" in result["error"].lower()
        
        # Try invalid date format
        result = await how_was_my_day.fn(date="invalid-date")
        assert result["success"] is False
        assert "invalid date" in result["error"].lower()
    
    async def test_mcp_tools_data_persistence(self):
        """Test that data persists across tool calls."""
        # Start session
        start_result = await start_working_on.fn(task="Persistence test")
        assert start_result["success"] is True
        
        # Set intention
        await set_morning_intention.fn(intention="Test data persistence")
        
        # Capture wins
        await capture_win.fn(win="First win")
        await capture_win.fn(win="Second win")
        
        # End session
        await asyncio.sleep(1)
        await end_work_session.fn()
        
        # Check daily summary includes all data
        summary = await how_was_my_day.fn()
        assert summary["success"] is True
        
        # Should have captured the session and wins
        progress = await daily_progress_prompt.fn()
        assert "first win" in progress.lower() or "second win" in progress.lower()
    
    async def test_prompts_reflect_current_state(self):
        """Test that prompts reflect current state."""
        # No active session initially
        active_prompt = await active_session_prompt.fn()
        assert "no active" in active_prompt.lower() or "not currently" in active_prompt.lower()
        
        # Start session
        await start_working_on.fn(task="Prompt state test")
        
        # Now should show active session
        active_prompt = await active_session_prompt.fn()
        assert "prompt state test" in active_prompt.lower()
        assert "duration" in active_prompt.lower() or "started" in active_prompt.lower()
        
        # Clean up
        await end_work_session.fn()
        
        # Should be back to no active session
        active_prompt = await active_session_prompt.fn()
        assert "no active" in active_prompt.lower() or "not currently" in active_prompt.lower()

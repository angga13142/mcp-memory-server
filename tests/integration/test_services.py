"""Integration tests for memory service operations."""

import pytest

from src.models import ProjectBrief
from src.services.memory_service import MemoryService


class TestMemoryServiceIntegration:
    """Integration tests for MemoryService."""

    @pytest.mark.asyncio
    async def test_project_brief_flow(self, memory_service: MemoryService):
        """Test full project brief workflow."""
        # Initially no brief
        brief = await memory_service.get_project_brief()
        assert brief is None

        # Create brief
        new_brief = ProjectBrief(
            name="Integration Test",
            description="Testing the memory service",
            goals=["Test all operations"],
        )
        await memory_service.save_project_brief(new_brief)

        # Retrieve and verify
        retrieved = await memory_service.get_project_brief()
        assert retrieved is not None
        assert retrieved.name == "Integration Test"

    @pytest.mark.asyncio
    async def test_context_update_flow(self, memory_service: MemoryService):
        """Test context update workflow."""
        # Update context
        await memory_service.update_active_context(
            current_task="Testing",
            related_files=["test.py", "conftest.py"],
            notes="Running integration tests",
        )

        # Retrieve and verify
        context = await memory_service.get_active_context()
        assert context.current_task == "Testing"
        assert len(context.related_files) == 2
        assert "Running integration tests" in context.notes

    @pytest.mark.asyncio
    async def test_decision_logging_flow(self, memory_service: MemoryService):
        """Test decision logging workflow."""
        # Log decision
        decision = await memory_service.log_decision(
            title="Use Integration Tests",
            decision="We will use pytest for integration testing",
            rationale="It integrates well with async code",
            tags=["testing", "quality"],
        )

        assert decision.id is not None

        # List all decisions
        all_decisions = await memory_service.list_decisions()
        assert len(all_decisions) >= 1

        # Get specific decision
        retrieved = await memory_service.get_decision(decision.id)
        assert retrieved is not None
        assert retrieved.title == "Use Integration Tests"

        # Get recent decisions
        recent = await memory_service.recent_decisions(3)
        assert len(recent) >= 1

    @pytest.mark.asyncio
    async def test_task_management_flow(self, memory_service: MemoryService):
        """Test task management workflow."""
        # Create task
        task = await memory_service.create_task(
            title="Write tests",
            description="Write integration tests",
            priority="high",
            tags=["testing"],
        )

        assert task.id is not None
        assert task.status == "next"

        # Update status to doing
        updated = await memory_service.update_task_status(task.id, "doing")
        assert updated is not None
        assert updated.status == "doing"

        # Complete task
        completed = await memory_service.update_task_status(task.id, "done")
        assert completed is not None
        assert completed.status == "done"
        assert completed.completed_at is not None

        # Get grouped tasks
        grouped = await memory_service.get_tasks_grouped()
        assert "done" in grouped
        assert len(grouped["done"]) >= 1

    @pytest.mark.asyncio
    async def test_memory_note_flow(self, memory_service: MemoryService):
        """Test generic memory note workflow."""
        # Add memory note
        entry = await memory_service.add_memory(
            content="This is a test note for semantic search",
            content_type="note",
            tags=["test", "search"],
        )

        assert entry.id is not None

        # Retrieve memory
        retrieved = await memory_service.get_memory(entry.id)
        assert retrieved is not None
        assert retrieved.content == "This is a test note for semantic search"


class TestSearchServiceIntegration:
    """Integration tests for SearchService."""

    @pytest.mark.asyncio
    async def test_search_after_adding_memories(
        self, memory_service: MemoryService, search_service
    ):
        """Test semantic search functionality."""
        # Add some memories
        await memory_service.add_memory(
            content="Python is a programming language",
            tags=["programming"],
        )
        await memory_service.add_memory(
            content="FastMCP is a framework for MCP servers",
            tags=["framework"],
        )
        await memory_service.add_memory(
            content="ChromaDB is a vector database",
            tags=["database"],
        )

        # Search
        results = await search_service.search("vector database", limit=2)

        assert len(results) >= 1
        # The ChromaDB entry should be most relevant
        assert any("ChromaDB" in r.get("content", "") for r in results)

    @pytest.mark.asyncio
    async def test_count(self, search_service):
        """Test counting memories."""
        count = await search_service.count()
        assert isinstance(count, int)
        assert count >= 0

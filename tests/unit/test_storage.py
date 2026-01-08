"""Unit tests for storage layer."""

import pytest
import pytest_asyncio

from src.models import ActiveContext, Decision, ProjectBrief, Task, TechStack
from src.models.project import TechStackItem
from src.storage.database import Database
from src.storage.repositories import (
    ContextRepository,
    DecisionRepository,
    ProjectRepository,
    TaskRepository,
)


class TestProjectRepository:
    """Tests for ProjectRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_brief(self, database: Database):
        """Test saving and retrieving project brief."""
        async with database.session() as session:
            repo = ProjectRepository(session)
            
            brief = ProjectBrief(
                name="Test Project",
                description="Test description",
                goals=["Goal 1"],
            )
            await repo.save_brief(brief)
        
        async with database.session() as session:
            repo = ProjectRepository(session)
            result = await repo.get_brief()
            
            assert result is not None
            assert result.name == "Test Project"
            assert result.description == "Test description"
            assert result.goals == ["Goal 1"]

    @pytest.mark.asyncio
    async def test_update_brief(self, database: Database):
        """Test updating project brief."""
        async with database.session() as session:
            repo = ProjectRepository(session)
            brief = ProjectBrief(name="Initial", description="Initial desc")
            await repo.save_brief(brief)
        
        async with database.session() as session:
            repo = ProjectRepository(session)
            updated = ProjectBrief(name="Updated", description="New desc")
            await repo.save_brief(updated)
        
        async with database.session() as session:
            repo = ProjectRepository(session)
            result = await repo.get_brief()
            assert result.name == "Updated"

    @pytest.mark.asyncio
    async def test_tech_stack(self, database: Database):
        """Test tech stack operations."""
        async with database.session() as session:
            repo = ProjectRepository(session)
            
            stack = TechStack(
                languages=["Python"],
                frameworks=[TechStackItem(name="FastMCP", version="2.14.0")],
                tools=["Docker"],
            )
            await repo.save_tech_stack(stack)
        
        async with database.session() as session:
            repo = ProjectRepository(session)
            result = await repo.get_tech_stack()
            
            assert result is not None
            assert "Python" in result.languages
            assert result.frameworks[0].name == "FastMCP"


class TestDecisionRepository:
    """Tests for DecisionRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get(self, database: Database):
        """Test saving and retrieving decision."""
        async with database.session() as session:
            repo = DecisionRepository(session)
            
            decision = Decision(
                title="Test Decision",
                decision="We decided X",
                rationale="Because Y",
                tags=["test"],
            )
            await repo.save(decision)
            decision_id = decision.id
        
        async with database.session() as session:
            repo = DecisionRepository(session)
            result = await repo.get(decision_id)
            
            assert result is not None
            assert result.title == "Test Decision"
            assert result.tags == ["test"]

    @pytest.mark.asyncio
    async def test_get_all(self, database: Database):
        """Test getting all decisions."""
        async with database.session() as session:
            repo = DecisionRepository(session)
            
            for i in range(3):
                await repo.save(Decision(
                    title=f"Decision {i}",
                    decision=f"D{i}",
                    rationale=f"R{i}",
                ))
        
        async with database.session() as session:
            repo = DecisionRepository(session)
            all_decisions = await repo.get_all()
            assert len(all_decisions) == 3

    @pytest.mark.asyncio
    async def test_recent(self, database: Database):
        """Test getting recent decisions."""
        async with database.session() as session:
            repo = DecisionRepository(session)
            
            for i in range(5):
                await repo.save(Decision(
                    title=f"Decision {i}",
                    decision=f"D{i}",
                    rationale=f"R{i}",
                ))
        
        async with database.session() as session:
            repo = DecisionRepository(session)
            recent = await repo.recent(3)
            assert len(recent) == 3


class TestContextRepository:
    """Tests for ContextRepository."""

    @pytest.mark.asyncio
    async def test_get_default(self, database: Database):
        """Test getting default context."""
        async with database.session() as session:
            repo = ContextRepository(session)
            context = await repo.get()
            
            assert context is not None
            assert context.current_task == ""

    @pytest.mark.asyncio
    async def test_save_and_get(self, database: Database):
        """Test saving and retrieving context."""
        async with database.session() as session:
            repo = ContextRepository(session)
            
            context = ActiveContext(
                current_task="Testing",
                related_files=["test.py"],
                notes="Test notes",
            )
            await repo.save(context)
        
        async with database.session() as session:
            repo = ContextRepository(session)
            result = await repo.get()
            
            assert result.current_task == "Testing"
            assert "test.py" in result.related_files


class TestTaskRepository:
    """Tests for TaskRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get(self, database: Database):
        """Test saving and retrieving task."""
        async with database.session() as session:
            repo = TaskRepository(session)
            
            task = Task(title="Test Task", priority="high")
            await repo.save(task)
            task_id = task.id
        
        async with database.session() as session:
            repo = TaskRepository(session)
            result = await repo.get(task_id)
            
            assert result is not None
            assert result.title == "Test Task"
            assert result.priority == "high"

    @pytest.mark.asyncio
    async def test_grouped_by_status(self, database: Database):
        """Test grouping tasks by status."""
        async with database.session() as session:
            repo = TaskRepository(session)
            
            await repo.save(Task(title="Done", status="done"))
            await repo.save(Task(title="Doing", status="doing"))
            await repo.save(Task(title="Next", status="next"))
        
        async with database.session() as session:
            repo = TaskRepository(session)
            grouped = await repo.grouped_by_status()
            
            assert len(grouped["done"]) == 1
            assert len(grouped["doing"]) == 1
            assert len(grouped["next"]) == 1

    @pytest.mark.asyncio
    async def test_delete(self, database: Database):
        """Test deleting a task."""
        async with database.session() as session:
            repo = TaskRepository(session)
            task = Task(title="To Delete")
            await repo.save(task)
            task_id = task.id
        
        async with database.session() as session:
            repo = TaskRepository(session)
            deleted = await repo.delete(task_id)
            assert deleted is True
        
        async with database.session() as session:
            repo = TaskRepository(session)
            result = await repo.get(task_id)
            assert result is None

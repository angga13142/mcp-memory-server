"""Memory service - core business logic for memory operations."""

from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from src.models import (
    ActiveContext,
    Decision,
    MemoryEntry,
    ProjectBrief,
    Task,
    TechStack,
)
from src.storage.database import Database
from src.storage.repositories import (
    ContextRepository,
    DecisionRepository,
    MemoryEntryRepository,
    ProjectRepository,
    TaskRepository,
)
from src.storage.vector_store import VectorMemoryStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryService:
    """Core memory management service.

    Provides a unified interface for all memory operations,
    coordinating between the database and vector store.
    """

    def __init__(self, database: Database, vector_store: VectorMemoryStore):
        self.database = database
        self.vector_store = vector_store

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _safe_vector_add(
        self, id: str, content: str, metadata: dict[str, Any]
    ) -> None:
        """Add to vector store with retry logic.

        Args:
            id: Memory ID
            content: Content to embed
            metadata: Metadata for filtering

        Raises:
            Exception: If all retries fail
        """
        try:
            await self.vector_store.add_memory(id, content, metadata)
        except Exception as e:
            logger.warning(f"Vector store add attempt failed for {id}: {e}")
            raise

    async def _add_to_vector_store_safe(
        self, id: str, content: str, metadata: dict[str, Any]
    ) -> None:
        """Safely add to vector store with retry and fallback.

        Args:
            id: Memory ID
            content: Content to embed
            metadata: Metadata for filtering
        """
        try:
            await self._safe_vector_add(id, content, metadata)
        except Exception as e:
            logger.error(f"Failed to add to vector store after retries (id={id}): {e}")
            # Continue - don't fail the operation if vector store fails

    # === Project Brief ===

    async def get_project_brief(self) -> ProjectBrief | None:
        """Get the project brief."""
        async with self.database.session() as session:
            repo = ProjectRepository(session)
            return await repo.get_brief()

    async def save_project_brief(self, brief: ProjectBrief) -> ProjectBrief:
        """Save or update the project brief."""
        async with self.database.session() as session:
            repo = ProjectRepository(session)
            result = await repo.save_brief(brief)

            # Index in vector store
            await self._add_to_vector_store_safe(
                id=f"project_brief",
                content=f"Project: {brief.name}\n{brief.description}\nGoals: {', '.join(brief.goals)}",
                metadata={"content_type": "project_brief", "version": brief.version},
            )

            logger.info(f"Saved project brief: {brief.name}")
            return result

    # === Tech Stack ===

    async def get_tech_stack(self) -> TechStack | None:
        """Get the tech stack."""
        async with self.database.session() as session:
            repo = ProjectRepository(session)
            return await repo.get_tech_stack()

    async def save_tech_stack(self, tech_stack: TechStack) -> TechStack:
        """Save or update the tech stack."""
        async with self.database.session() as session:
            repo = ProjectRepository(session)
            result = await repo.save_tech_stack(tech_stack)

            # Index in vector store
            frameworks_str = ", ".join(f.name for f in tech_stack.frameworks)
            content = f"Languages: {', '.join(tech_stack.languages)}\nFrameworks: {frameworks_str}\nTools: {', '.join(tech_stack.tools)}"
            await self._add_to_vector_store_safe(
                id="tech_stack",
                content=content,
                metadata={"content_type": "tech_stack"},
            )

            logger.info("Saved tech stack")
            return result

    # === Active Context ===

    async def get_active_context(self) -> ActiveContext:
        """Get the active context."""
        async with self.database.session() as session:
            repo = ContextRepository(session)
            return await repo.get()

    async def update_active_context(
        self,
        current_task: str | None = None,
        related_files: list[str] | None = None,
        relevant_decisions: list[str] | None = None,
        notes: str | None = None,
        working_branch: str | None = None,
    ) -> ActiveContext:
        """Update the active context."""
        async with self.database.session() as session:
            repo = ContextRepository(session)
            context = await repo.get()
            context.update(
                current_task=current_task,
                related_files=related_files,
                relevant_decisions=relevant_decisions,
                notes=notes,
                working_branch=working_branch,
            )
            result = await repo.save(context)

            # Index in vector store
            if current_task or notes:
                await self._add_to_vector_store_safe(
                    id="active_context",
                    content=context.to_prompt(),
                    metadata={"content_type": "active_context"},
                )

            logger.info(f"Updated active context: {current_task or 'cleared'}")
            return result

    # === Decisions ===

    async def list_decisions(self) -> list[Decision]:
        """List all decisions."""
        async with self.database.session() as session:
            repo = DecisionRepository(session)
            return await repo.get_all()

    async def get_decision(self, decision_id: str) -> Decision | None:
        """Get a specific decision."""
        async with self.database.session() as session:
            repo = DecisionRepository(session)
            return await repo.get(decision_id)

    async def log_decision(
        self,
        title: str,
        decision: str,
        rationale: str,
        alternatives_considered: list[str] | None = None,
        consequences: list[str] | None = None,
        tags: list[str] | None = None,
        created_by: str = "user",
    ) -> Decision:
        """Log a new architectural decision."""
        new_decision = Decision(
            title=title,
            decision=decision,
            rationale=rationale,
            alternatives_considered=alternatives_considered or [],
            consequences=consequences or [],
            tags=tags or [],
            created_by=created_by,
        )

        async with self.database.session() as session:
            repo = DecisionRepository(session)
            result = await repo.save(new_decision)

            # Index in vector store
            content = f"Decision: {title}\n{decision}\nRationale: {rationale}"
            await self._add_to_vector_store_safe(
                id=f"decision_{result.id}",
                content=content,
                metadata={
                    "content_type": "decision",
                    "source_id": result.id,
                    "tags": ",".join(tags or []),
                },
            )

            logger.info(f"Logged decision: {title} ({result.id})")
            return result

    async def recent_decisions(self, limit: int = 5) -> list[Decision]:
        """Get recent decisions."""
        async with self.database.session() as session:
            repo = DecisionRepository(session)
            return await repo.recent(limit)

    # === Tasks ===

    async def list_tasks(self) -> list[Task]:
        """List all tasks."""
        async with self.database.session() as session:
            repo = TaskRepository(session)
            return await repo.get_all()

    async def get_task(self, task_id: str) -> Task | None:
        """Get a specific task."""
        async with self.database.session() as session:
            repo = TaskRepository(session)
            return await repo.get(task_id)

    async def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        tags: list[str] | None = None,
        parent_id: str | None = None,
    ) -> Task:
        """Create a new task."""
        new_task = Task(
            title=title,
            description=description,
            priority=priority,  # type: ignore
            tags=tags or [],
            parent_id=parent_id,
        )

        async with self.database.session() as session:
            repo = TaskRepository(session)
            result = await repo.save(new_task)

            # Index in vector store
            content = f"Task: {title}\n{description}"
            await self._add_to_vector_store_safe(
                id=f"task_{result.id}",
                content=content,
                metadata={
                    "content_type": "task",
                    "source_id": result.id,
                    "priority": priority,
                    "status": "next",
                },
            )

            logger.info(f"Created task: {title} ({result.id})")
            return result

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        blocked_reason: str | None = None,
    ) -> Task | None:
        """Update a task's status."""
        async with self.database.session() as session:
            repo = TaskRepository(session)
            task = await repo.get(task_id)
            if not task:
                return None

            task.update_status(status, blocked_reason)  # type: ignore
            result = await repo.save(task)

            # Update vector store metadata
            content = f"Task: {task.title}\n{task.description}"
            await self._add_to_vector_store_safe(
                id=f"task_{result.id}",
                content=content,
                metadata={
                    "content_type": "task",
                    "source_id": result.id,
                    "priority": task.priority,
                    "status": status,
                },
            )

            logger.info(f"Updated task status: {task_id} -> {status}")
            return result

    async def get_tasks_grouped(self) -> dict[str, list[Task]]:
        """Get tasks grouped by status."""
        async with self.database.session() as session:
            repo = TaskRepository(session)
            return await repo.grouped_by_status()

    # === Memory Entries ===

    async def add_memory(
        self,
        content: str,
        content_type: str = "note",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Add a generic memory entry."""
        entry = MemoryEntry(
            content=content,
            content_type=content_type,
            tags=tags or [],
            metadata=metadata or {},
        )

        async with self.database.session() as session:
            repo = MemoryEntryRepository(session)
            result = await repo.save(entry)

            # Index in vector store
            await self._add_to_vector_store_safe(
                id=f"memory_{result.id}",
                content=content,
                metadata={
                    "content_type": content_type,
                    "source_id": result.id,
                    "tags": ",".join(tags or []),
                    **(metadata or {}),
                },
            )

            logger.info(f"Added memory: {content_type} ({result.id})")
            return result

    async def get_memory(self, entry_id: str) -> MemoryEntry | None:
        """Get a specific memory entry."""
        async with self.database.session() as session:
            repo = MemoryEntryRepository(session)
            return await repo.get(entry_id)

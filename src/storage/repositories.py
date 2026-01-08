"""Repository layer for database operations."""

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    ActiveContext,
    Decision,
    MemoryEntry,
    ProjectBrief,
    Task,
    TechStack,
)
from src.models.journal import DailyJournal, SessionReflection, WorkSession, generate_id
from src.models.project import TechStackItem
from src.storage.database import (
    ActiveContextDB,
    DailyJournalDB,
    DecisionDB,
    MemoryEntryDB,
    ProjectBriefDB,
    SessionReflectionDB,
    TaskDB,
    TechStackDB,
    WorkSessionDB,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ProjectRepository:
    """Repository for project-related data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_brief(self) -> ProjectBrief | None:
        """Get the project brief (singleton)."""
        result = await self.session.execute(select(ProjectBriefDB).limit(1))
        row = result.scalar_one_or_none()
        if row:
            return ProjectBrief(
                name=row.name,
                description=row.description or "",
                goals=row.goals or [],
                version=row.version or "1.0.0",
                created_at=row.created_at,
            )
        return None

    async def save_brief(self, brief: ProjectBrief) -> ProjectBrief:
        """Save or update the project brief."""
        result = await self.session.execute(select(ProjectBriefDB).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = brief.name
            existing.description = brief.description
            existing.goals = brief.goals
            existing.version = brief.version
        else:
            db_brief = ProjectBriefDB(
                name=brief.name,
                description=brief.description,
                goals=brief.goals,
                version=brief.version,
                created_at=brief.created_at,
            )
            self.session.add(db_brief)
        return brief

    async def get_tech_stack(self) -> TechStack | None:
        """Get the tech stack (singleton)."""
        result = await self.session.execute(select(TechStackDB).limit(1))
        row = result.scalar_one_or_none()
        if row:
            frameworks = [
                TechStackItem(**f)
                if isinstance(f, dict)
                else TechStackItem(name=str(f))
                for f in (row.frameworks or [])
            ]
            return TechStack(
                languages=row.languages or [],
                frameworks=frameworks,
                tools=row.tools or [],
                last_updated=row.last_updated,
            )
        return None

    async def save_tech_stack(self, tech_stack: TechStack) -> TechStack:
        """Save or update the tech stack."""
        result = await self.session.execute(select(TechStackDB).limit(1))
        existing = result.scalar_one_or_none()

        frameworks_data = [f.model_dump() for f in tech_stack.frameworks]

        if existing:
            existing.languages = tech_stack.languages
            existing.frameworks = frameworks_data
            existing.tools = tech_stack.tools
            existing.last_updated = tech_stack.last_updated
        else:
            db_tech = TechStackDB(
                languages=tech_stack.languages,
                frameworks=frameworks_data,
                tools=tech_stack.tools,
                last_updated=tech_stack.last_updated,
            )
            self.session.add(db_tech)
        return tech_stack


class DecisionRepository:
    """Repository for decision logging."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Decision]:
        """Get all decisions."""
        result = await self.session.execute(
            select(DecisionDB).order_by(DecisionDB.created_at.desc())
        )
        rows = result.scalars().all()
        return [self._to_model(row) for row in rows]

    async def get(self, decision_id: str) -> Decision | None:
        """Get a decision by ID."""
        result = await self.session.execute(
            select(DecisionDB).where(DecisionDB.id == decision_id)
        )
        row = result.scalar_one_or_none()
        return self._to_model(row) if row else None

    async def save(self, decision: Decision) -> Decision:
        """Save a new decision or update existing."""
        existing = await self.get(decision.id)
        if existing:
            await self.session.execute(
                update(DecisionDB)
                .where(DecisionDB.id == decision.id)
                .values(
                    title=decision.title,
                    decision=decision.decision,
                    rationale=decision.rationale,
                    alternatives_considered=decision.alternatives_considered,
                    consequences=decision.consequences,
                    tags=decision.tags,
                    status=decision.status,
                    superseded_by=decision.superseded_by,
                )
            )
        else:
            db_decision = DecisionDB(
                id=decision.id,
                title=decision.title,
                decision=decision.decision,
                rationale=decision.rationale,
                alternatives_considered=decision.alternatives_considered,
                consequences=decision.consequences,
                tags=decision.tags,
                status=decision.status,
                created_at=decision.created_at,
                created_by=decision.created_by,
                superseded_by=decision.superseded_by,
            )
            self.session.add(db_decision)
        return decision

    async def delete(self, decision_id: str) -> bool:
        """Delete a decision."""
        result = await self.session.execute(
            delete(DecisionDB).where(DecisionDB.id == decision_id)
        )
        return result.rowcount > 0

    async def filter_by_tag(self, tag: str) -> list[Decision]:
        """Get decisions with a specific tag."""
        all_decisions = await self.get_all()
        return [d for d in all_decisions if tag in d.tags]

    async def recent(self, limit: int = 5) -> list[Decision]:
        """Get most recent decisions."""
        result = await self.session.execute(
            select(DecisionDB).order_by(DecisionDB.created_at.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [self._to_model(row) for row in rows]

    def _to_model(self, row: DecisionDB) -> Decision:
        """Convert DB row to Pydantic model."""
        return Decision(
            id=row.id,
            title=row.title,
            decision=row.decision,
            rationale=row.rationale or "",
            alternatives_considered=row.alternatives_considered or [],
            consequences=row.consequences or [],
            tags=row.tags or [],
            status=row.status or "accepted",
            created_at=row.created_at,
            created_by=row.created_by or "user",
            superseded_by=row.superseded_by,
        )


class ContextRepository:
    """Repository for active context (singleton)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> ActiveContext:
        """Get the active context."""
        result = await self.session.execute(select(ActiveContextDB).limit(1))
        row = result.scalar_one_or_none()
        if row:
            return ActiveContext(
                current_task=row.current_task or "",
                related_files=row.related_files or [],
                relevant_decisions=row.relevant_decisions or [],
                notes=row.notes or "",
                working_branch=row.working_branch or "",
                session_id=row.session_id or "",
                last_updated=row.last_updated,
            )
        return ActiveContext()

    async def save(self, context: ActiveContext) -> ActiveContext:
        """Save or update the active context with optimistic locking.

        Raises:
            IntegrityError: If context was modified by another transaction
        """
        max_retries = 3
        for attempt in range(max_retries):
            result = await self.session.execute(select(ActiveContextDB).limit(1))
            existing = result.scalar_one_or_none()

            if existing:
                # Optimistic locking - update only if version matches
                update_result = await self.session.execute(
                    update(ActiveContextDB)
                    .where(ActiveContextDB.id == existing.id)
                    .where(ActiveContextDB.version == existing.version)
                    .values(
                        current_task=context.current_task,
                        related_files=context.related_files,
                        relevant_decisions=context.relevant_decisions,
                        notes=context.notes,
                        working_branch=context.working_branch,
                        session_id=context.session_id,
                        last_updated=context.last_updated,
                        version=existing.version + 1,
                    )
                )

                if update_result.rowcount == 0:
                    # Version mismatch - context was modified
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Context version conflict, retry {attempt + 1}/{max_retries}"
                        )
                        await self.session.rollback()
                        continue
                    else:
                        raise IntegrityError(
                            "Context was modified by another transaction", None, None
                        )
            else:
                db_context = ActiveContextDB(
                    id=1,
                    current_task=context.current_task,
                    related_files=context.related_files,
                    relevant_decisions=context.relevant_decisions,
                    notes=context.notes,
                    working_branch=context.working_branch,
                    session_id=context.session_id,
                    last_updated=context.last_updated,
                    version=0,
                )
                self.session.add(db_context)

            return context

        return context
        return context


class TaskRepository:
    """Repository for task management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Task]:
        """Get all tasks."""
        result = await self.session.execute(
            select(TaskDB).order_by(TaskDB.created_at.desc())
        )
        rows = result.scalars().all()
        return [self._to_model(row) for row in rows]

    async def get(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        result = await self.session.execute(select(TaskDB).where(TaskDB.id == task_id))
        row = result.scalar_one_or_none()
        return self._to_model(row) if row else None

    async def save(self, task: Task) -> Task:
        """Save a new task or update existing."""
        existing = await self.get(task.id)
        if existing:
            await self.session.execute(
                update(TaskDB)
                .where(TaskDB.id == task.id)
                .values(
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    priority=task.priority,
                    tags=task.tags,
                    parent_id=task.parent_id,
                    updated_at=datetime.now(UTC),
                    completed_at=task.completed_at,
                    blocked_reason=task.blocked_reason,
                )
            )
        else:
            db_task = TaskDB(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                tags=task.tags,
                parent_id=task.parent_id,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at,
                blocked_reason=task.blocked_reason,
            )
            self.session.add(db_task)
        return task

    async def delete(self, task_id: str) -> bool:
        """Delete a task."""
        result = await self.session.execute(delete(TaskDB).where(TaskDB.id == task_id))
        return result.rowcount > 0

    async def by_status(self, status: str) -> list[Task]:
        """Get tasks by status."""
        result = await self.session.execute(
            select(TaskDB)
            .where(TaskDB.status == status)
            .order_by(TaskDB.created_at.desc())
        )
        rows = result.scalars().all()
        return [self._to_model(row) for row in rows]

    async def grouped_by_status(self) -> dict[str, list[Task]]:
        """Get tasks grouped by status."""
        all_tasks = await self.get_all()
        return {
            "done": [t for t in all_tasks if t.status == "done"],
            "doing": [t for t in all_tasks if t.status == "doing"],
            "next": [t for t in all_tasks if t.status == "next"],
            "blocked": [t for t in all_tasks if t.status == "blocked"],
        }

    def _to_model(self, row: TaskDB) -> Task:
        """Convert DB row to Pydantic model."""
        return Task(
            id=row.id,
            title=row.title,
            description=row.description or "",
            status=row.status or "next",
            priority=row.priority or "medium",
            tags=row.tags or [],
            parent_id=row.parent_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            completed_at=row.completed_at,
            blocked_reason=row.blocked_reason,
        )


class MemoryEntryRepository:
    """Repository for memory entries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[MemoryEntry]:
        """Get all memory entries."""
        result = await self.session.execute(
            select(MemoryEntryDB).order_by(MemoryEntryDB.created_at.desc())
        )
        rows = result.scalars().all()
        return [self._to_model(row) for row in rows]

    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Get a memory entry by ID."""
        result = await self.session.execute(
            select(MemoryEntryDB).where(MemoryEntryDB.id == entry_id)
        )
        row = result.scalar_one_or_none()
        return self._to_model(row) if row else None

    async def save(self, entry: MemoryEntry) -> MemoryEntry:
        """Save a new memory entry or update existing."""
        existing = await self.get(entry.id)
        if existing:
            await self.session.execute(
                update(MemoryEntryDB)
                .where(MemoryEntryDB.id == entry.id)
                .values(
                    content=entry.content,
                    content_type=entry.content_type,
                    source_id=entry.source_id,
                    entry_metadata=entry.metadata,
                    tags=entry.tags,
                    updated_at=datetime.now(UTC),
                )
            )
        else:
            db_entry = MemoryEntryDB(
                id=entry.id,
                content=entry.content,
                content_type=entry.content_type,
                source_id=entry.source_id,
                entry_metadata=entry.metadata,
                tags=entry.tags,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            )
            self.session.add(db_entry)
        return entry

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        result = await self.session.execute(
            delete(MemoryEntryDB).where(MemoryEntryDB.id == entry_id)
        )
        return result.rowcount > 0

    def _to_model(self, row: MemoryEntryDB) -> MemoryEntry:
        """Convert DB row to Pydantic model."""
        return MemoryEntry(
            id=row.id,
            content=row.content,
            content_type=row.content_type or "note",
            source_id=row.source_id,
            metadata=row.entry_metadata or {},
            tags=row.tags or [],
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class JournalRepository:
    """Repository for journal operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_today(self) -> DailyJournal:
        """Get today's journal or create if doesn't exist."""
        today = datetime.now(UTC).date()

        result = await self.session.execute(
            select(DailyJournalDB).where(DailyJournalDB.date == today)
        )
        db_journal = result.scalar_one_or_none()

        if not db_journal:
            # Create new journal for today
            db_journal = DailyJournalDB(id=generate_id(), date=today)
            self.session.add(db_journal)
            await self.session.flush()

        return await self._to_model(db_journal)

    async def get_by_date(self, date: datetime.date) -> DailyJournal | None:
        """Get journal for specific date."""
        result = await self.session.execute(
            select(DailyJournalDB).where(DailyJournalDB.date == date)
        )
        db_journal = result.scalar_one_or_none()

        if db_journal:
            return await self._to_model(db_journal)
        return None

    async def save(self, journal: DailyJournal) -> DailyJournal:
        """Save or update journal."""
        result = await self.session.execute(
            select(DailyJournalDB).where(DailyJournalDB.date == journal.date)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.morning_intention = journal.morning_intention
            existing.end_of_day_reflection = journal.end_of_day_reflection
            existing.energy_level = journal.energy_level
            existing.mood = journal.mood
            existing.wins = journal.wins
            existing.updated_at = datetime.now(UTC)
        else:
            # Create new
            db_journal = DailyJournalDB(
                id=journal.id,
                date=journal.date,
                morning_intention=journal.morning_intention,
                end_of_day_reflection=journal.end_of_day_reflection,
                energy_level=journal.energy_level,
                mood=journal.mood,
                wins=journal.wins,
                created_at=journal.created_at,
                updated_at=journal.updated_at,
            )
            self.session.add(db_journal)

        return journal

    async def add_session(self, journal_id: str, session: WorkSession) -> WorkSession:
        """Add work session to journal."""
        db_session = WorkSessionDB(
            id=session.id,
            journal_id=journal_id,
            start_time=session.start_time,
            end_time=session.end_time,
            task=session.task,
            files_touched=session.files_touched,
            decisions_made=session.decisions_made,
            notes=session.notes,
            learnings=session.learnings,
            challenges=session.challenges,
            created_at=session.start_time,
        )
        self.session.add(db_session)
        await self.session.flush()

        return session

    async def update_session(self, session: WorkSession) -> WorkSession:
        """Update existing work session."""
        result = await self.session.execute(
            select(WorkSessionDB).where(WorkSessionDB.id == session.id)
        )
        db_session = result.scalar_one_or_none()

        if db_session:
            db_session.end_time = session.end_time
            db_session.files_touched = session.files_touched
            db_session.decisions_made = session.decisions_made
            db_session.notes = session.notes
            db_session.learnings = session.learnings
            db_session.challenges = session.challenges

        return session

    async def save_reflection(self, reflection: SessionReflection) -> SessionReflection:
        """Save session reflection."""
        db_reflection = SessionReflectionDB(
            id=generate_id(),
            session_id=reflection.session_id,
            reflection_text=reflection.reflection_text,
            key_insights=reflection.key_insights,
            related_memories=reflection.related_memories,
            created_at=reflection.created_at,
        )
        self.session.add(db_reflection)
        await self.session.flush()

        return reflection

    async def get_sessions_by_date(self, date: datetime.date) -> list[WorkSession]:
        """Get all sessions for a specific date."""
        result = await self.session.execute(
            select(WorkSessionDB)
            .join(DailyJournalDB)
            .where(DailyJournalDB.date == date)
            .order_by(WorkSessionDB.start_time)
        )
        db_sessions = result.scalars().all()

        return [self._session_to_model(s) for s in db_sessions]

    async def get_recent_journals(self, days: int = 7) -> list[DailyJournal]:
        """Get journals for recent days."""
        from datetime import timedelta

        start_date = datetime.now(UTC).date() - timedelta(days=days)

        result = await self.session.execute(
            select(DailyJournalDB)
            .where(DailyJournalDB.date >= start_date)
            .order_by(DailyJournalDB.date.desc())
        )
        db_journals = result.scalars().all()

        journals = []
        for db_journal in db_journals:
            journals.append(await self._to_model(db_journal))

        return journals

    def _ensure_utc(self, dt: datetime | None) -> datetime | None:
        """Ensure datetime is timezone-aware UTC."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    async def _to_model(self, db_journal: DailyJournalDB) -> DailyJournal:
        """Convert DB model to Pydantic model."""
        # Load sessions
        result = await self.session.execute(
            select(WorkSessionDB)
            .where(WorkSessionDB.journal_id == db_journal.id)
            .order_by(WorkSessionDB.start_time)
        )
        db_sessions = result.scalars().all()

        sessions = [self._session_to_model(s) for s in db_sessions]

        return DailyJournal(
            id=db_journal.id,
            date=db_journal.date,
            morning_intention=db_journal.morning_intention or "",
            work_sessions=sessions,
            end_of_day_reflection=db_journal.end_of_day_reflection or "",
            energy_level=db_journal.energy_level or 3,
            mood=db_journal.mood or "",
            wins=db_journal.wins or [],
            created_at=self._ensure_utc(db_journal.created_at),
            updated_at=self._ensure_utc(db_journal.updated_at),
        )

    def _session_to_model(self, db_session: WorkSessionDB) -> WorkSession:
        """Convert DB session to Pydantic model."""
        return WorkSession(
            id=db_session.id,
            start_time=self._ensure_utc(db_session.start_time),
            end_time=self._ensure_utc(db_session.end_time),
            task=db_session.task,
            files_touched=db_session.files_touched or [],
            decisions_made=db_session.decisions_made or [],
            notes=db_session.notes or "",
            learnings=db_session.learnings or [],
            challenges=db_session.challenges or [],
        )

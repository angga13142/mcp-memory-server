"""SQLAlchemy database setup and session management."""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.utils.config import Settings, get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


# === Database Models ===


class ProjectBriefDB(Base):
    """Project brief database table."""

    __tablename__ = "project_brief"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    goals = Column(JSON, default=list)
    version = Column(String(50), default="1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)


class TechStackDB(Base):
    """Tech stack database table."""

    __tablename__ = "tech_stack"

    id = Column(Integer, primary_key=True)
    languages = Column(JSON, default=list)
    frameworks = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DecisionDB(Base):
    """Decision log database table."""

    __tablename__ = "decisions"

    id = Column(String(50), primary_key=True)
    title = Column(String(500), nullable=False)
    decision = Column(Text, nullable=False)
    rationale = Column(Text, default="")
    alternatives_considered = Column(JSON, default=list)
    consequences = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    status = Column(String(50), default="accepted")
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default="user")
    superseded_by = Column(String(50), nullable=True)


class ActiveContextDB(Base):
    """Active context database table (singleton)."""

    __tablename__ = "active_context"

    id = Column(Integer, primary_key=True, default=1)
    current_task = Column(Text, default="")
    related_files = Column(JSON, default=list)
    relevant_decisions = Column(JSON, default=list)
    notes = Column(Text, default="")
    working_branch = Column(String(255), default="")
    session_id = Column(String(100), default="")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskDB(Base):
    """Task database table."""

    __tablename__ = "tasks"

    id = Column(String(50), primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="next")
    priority = Column(String(50), default="medium")
    tags = Column(JSON, default=list)
    parent_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    blocked_reason = Column(Text, nullable=True)


class MemoryEntryDB(Base):
    """Memory entry database table."""

    __tablename__ = "memory_entries"

    id = Column(String(50), primary_key=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(100), default="note")
    source_id = Column(String(50), nullable=True)
    entry_metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemPatternDB(Base):
    """System patterns database table."""

    __tablename__ = "system_patterns"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    example = Column(Text, default="")
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


# === Database Manager ===


class Database:
    """Async database manager."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._engine = None
        self._session_factory = None

    async def init(self) -> None:
        """Initialize database connection and create tables."""
        db_url = self.settings.storage.sqlite.database_url

        # Ensure data directory exists
        if ":///" in db_url:
            db_path = db_url.split(":///")[-1]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_async_engine(
            db_url,
            echo=self.settings.storage.sqlite.echo,
        )

        # Enable WAL mode for SQLite (better concurrent access)
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info(f"Database initialized: {db_url}")

    async def close(self) -> None:
        """Close database connection."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connection closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Global database instance
_database: Database | None = None


async def get_database(settings: Settings | None = None) -> Database:
    """Get or create global database instance."""
    global _database
    if _database is None:
        _database = Database(settings)
        await _database.init()
    return _database


async def close_database() -> None:
    """Close global database instance."""
    global _database
    if _database:
        await _database.close()
        _database = None

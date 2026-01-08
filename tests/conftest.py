"""Pytest fixtures for MCP Memory Server tests."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from src.storage.database import Database
from src.storage.vector_store import VectorMemoryStore
from src.services.memory_service import MemoryService
from src.services.search_service import SearchService
from src.utils.config import Settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings with temporary directories."""
    settings = Settings()
    settings.storage.sqlite.database_url = f"sqlite+aiosqlite:///{temp_dir}/test.db"
    settings.storage.chroma.persist_directory = str(temp_dir / "chroma")
    return settings


@pytest_asyncio.fixture
async def database(test_settings: Settings) -> AsyncGenerator[Database, None]:
    """Create a test database instance."""
    db = Database(test_settings)
    await db.init()
    yield db
    await db.close()


@pytest_asyncio.fixture
async def vector_store(test_settings: Settings) -> AsyncGenerator[VectorMemoryStore, None]:
    """Create a test vector store instance."""
    store = VectorMemoryStore(test_settings)
    await store.init()
    yield store


@pytest_asyncio.fixture
async def memory_service(
    database: Database, vector_store: VectorMemoryStore
) -> MemoryService:
    """Create a test memory service instance."""
    return MemoryService(database, vector_store)


@pytest_asyncio.fixture
async def search_service(vector_store: VectorMemoryStore) -> SearchService:
    """Create a test search service instance."""
    return SearchService(vector_store)

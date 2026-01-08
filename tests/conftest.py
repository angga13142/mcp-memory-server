"""Pytest fixtures for MCP Memory Server tests."""

import asyncio
import sqlite3
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.services.memory_service import MemoryService
from src.services.search_service import SearchService
from src.storage.database import Base, Database
from src.storage.vector_store import VectorMemoryStore
from src.utils.config import Settings

# ============================================
# Test Configuration
# ============================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "load: Load/performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_services: Requires external services")


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add markers based on test location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "load" in str(item.fspath):
            item.add_marker(pytest.mark.load)


# ============================================
# Async Fixtures
# ============================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def event_loop_policy():
    """Event loop policy for tests."""
    return asyncio.get_event_loop_policy()


# ============================================
# Temporary Directory Fixtures
# ============================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir) -> Path:
    """Create temporary file."""
    file_path = temp_dir / "test_file.txt"
    file_path.touch()
    return file_path


# ============================================
# Settings and Database Fixtures
# ============================================


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

    # Force table creation for tests
    async with db._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield db
    await db.close()


@pytest_asyncio.fixture
async def vector_store(
    test_settings: Settings,
) -> AsyncGenerator[VectorMemoryStore, None]:
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


# ============================================
# SQLite Database Fixtures
# ============================================


@pytest.fixture
def test_db_path(temp_dir) -> Path:
    """Create temporary test database path."""
    return temp_dir / "test_memory.db"


@pytest.fixture
def test_db(test_db_path) -> Generator[sqlite3.Connection, None, None]:
    """Create test database with schema."""
    conn = sqlite3.connect(str(test_db_path))

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS journal_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_date TEXT NOT NULL,
            content TEXT,
            reflection TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            content TEXT NOT NULL,
            embedding_id TEXT,
            memory_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES journal_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            learning_text TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES journal_sessions(id)
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_user ON journal_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id);
    """
    )

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def populated_db(test_db) -> sqlite3.Connection:
    """Database with test data."""
    test_data = [
        ("user1", "2025-01-01", "First journal entry", "First reflection"),
        ("user1", "2025-01-02", "Second journal entry", "Second reflection"),
        ("user2", "2025-01-01", "Another user entry", "Another reflection"),
    ]

    for user_id, date, content, reflection in test_data:
        cursor = test_db.execute(
            "INSERT INTO journal_sessions (user_id, session_date, content, reflection) VALUES (?, ?, ?, ?)",
            (user_id, date, content, reflection),
        )
        session_id = cursor.lastrowid

        test_db.execute(
            "INSERT INTO memories (session_id, content, memory_type) VALUES (?, ?, ?)",
            (session_id, f"Memory for session {session_id}", "episodic"),
        )

        test_db.execute(
            "INSERT INTO learnings (session_id, learning_text, category) VALUES (?, ?, ?)",
            (session_id, f"Learning from session {session_id}", "technical"),
        )

    test_db.commit()
    return test_db


# ============================================
# Metrics Fixtures
# ============================================


@pytest.fixture
def mock_prometheus_registry():
    """Mock Prometheus registry."""
    from prometheus_client import CollectorRegistry

    return CollectorRegistry()


@pytest.fixture
def journal_metrics(mock_prometheus_registry):
    """Journal metrics instance."""
    from src.monitoring.metrics.journal_metrics import JournalMetrics

    metrics = JournalMetrics()
    metrics.registry = mock_prometheus_registry
    metrics.register()
    return metrics


@pytest.fixture
def database_metrics(mock_prometheus_registry):
    """Database metrics instance."""
    from src.monitoring.metrics.database_metrics import DatabaseMetrics

    metrics = DatabaseMetrics()
    metrics.registry = mock_prometheus_registry
    metrics.register()
    return metrics


@pytest.fixture
def vector_metrics(mock_prometheus_registry):
    """Vector store metrics instance."""
    from src.monitoring.metrics.vector_store_metrics import VectorStoreMetrics

    metrics = VectorStoreMetrics()
    metrics.registry = mock_prometheus_registry
    metrics.register()
    return metrics


# ============================================
# Mock Service Fixtures
# ============================================


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = 0
    return mock_client


@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB client."""
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.add.return_value = None
    mock_collection.query.return_value = {"documents": [], "distances": []}

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    return mock_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Mock AI response"))]
    mock_response.usage = MagicMock(total_tokens=100)

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [MagicMock(embedding=[0.1] * 1536)]
    mock_client.embeddings.create.return_value = mock_embedding_response

    return mock_client


# ============================================
# API Client Fixtures
# ============================================


@pytest.fixture
def api_base_url():
    """Base URL for API."""
    return "http://localhost:8080"


@pytest.fixture
def prometheus_url():
    """Prometheus URL."""
    return "http://localhost:9090"


@pytest.fixture
def grafana_url():
    """Grafana URL."""
    return "http://localhost:3000"


@pytest.fixture
def grafana_auth():
    """Grafana authentication."""
    return ("admin", "admin")


# ============================================
# Test Data Fixtures
# ============================================


@pytest.fixture
def sample_journal_entry() -> dict[str, Any]:
    """Sample journal entry data."""
    return {
        "user_id": "test_user",
        "session_date": "2025-01-08",
        "content": "Today I worked on testing. Learned about fixtures and mocks.",
        "mood": "productive",
        "tags": ["testing", "learning"],
    }


@pytest.fixture
def sample_reflection() -> str:
    """Sample reflection text."""
    return """
    Today's session showed good progress in understanding test infrastructure.
    Key learnings: Fixtures provide reusable test components.
    Challenge: Managing test data lifecycle.
    Win: Created comprehensive test suite.
    """


@pytest.fixture
def sample_memories() -> list:
    """Sample memories list."""
    return [
        {
            "content": "Learned about pytest fixtures",
            "type": "learning",
            "importance": 0.8,
        },
        {
            "content": "Challenge with async tests",
            "type": "challenge",
            "importance": 0.6,
        },
        {
            "content": "Successfully implemented mocks",
            "type": "achievement",
            "importance": 0.9,
        },
    ]


# ============================================
# Environment Fixtures
# ============================================


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables."""
    env_vars = {
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "sqlite:///test.db",
        "REDIS_URL": "redis://localhost:6379/0",
        "OPENAI_API_KEY": "test-key-123",
        "PROMETHEUS_PORT": "9090",
        "GRAFANA_PASSWORD": "test-password",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


# ============================================
# Cleanup Fixtures
# ============================================


@pytest.fixture(autouse=True)
def cleanup_metrics():
    """Cleanup metrics after each test."""
    yield


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances."""
    yield

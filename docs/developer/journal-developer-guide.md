# Daily Journal - Developer Guide

## Architecture Overview

```
MCP Client → FastMCP Server → Service Layer → Repository → Database
                           ↓                              ↓
                     Vector Store ← ← ← ← ← ← ← ← ← ← ← ←
```

### Component Flow

1. **MCP Client** - Claude Desktop or custom client
2. **FastMCP Server** - Tools, prompts, resources endpoints
3. **Service Layer** - Business logic and orchestration
4. **Repository Layer** - Data access abstraction
5. **Database** - SQLite for structured data
6. **Vector Store** - ChromaDB for semantic search

---

## Core Components

### 1. Models (`src/models/journal.py`)

Pydantic models with validation and computed properties.

**Key Models:**

- `WorkSession` - Individual work session
- `DailyJournal` - Daily journal aggregation
- `SessionReflection` - AI-generated reflection

**Example:**

```python
class WorkSession(BaseModel):
    task: str = Field(min_length=1, max_length=500)
    start_time: datetime
    end_time: datetime | None = None

    @property
    def duration_minutes(self) -> int:
        if not self.end_time:
            return 0
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
```

---

### 2. Database Layer (`src/storage/`)

**Database (`database.py`):**

- SQLAlchemy async engine
- Connection pooling
- Transaction management

**Repositories (`repositories.py`):**

- `JournalRepository` - CRUD operations for journals
- Repository pattern for data access
- Type-safe queries

**Example:**

```python
async with database.session() as session:
    repo = JournalRepository(session)
    journal = await repo.get_or_create_today()
```

---

### 3. Service Layer (`src/services/journal_service.py`)

Business logic orchestration.

**JournalService responsibilities:**

- Session lifecycle management
- AI reflection generation
- Daily summary creation
- Validation and error handling

**Key methods:**

- `start_work_session(task)` - Create new session
- `end_work_session(...)` - Complete session, generate reflection
- `generate_daily_summary()` - Create day summary
- `get_morning_briefing()` - Morning context

---

### 4. MCP Interface (`src/server.py`)

FastMCP tools, prompts, and resources.

**Tools:**

```python
@mcp.tool()
async def start_working_on(task: str) -> dict[str, Any]:
    """Start a work session."""
    journal_service = await get_journal_service()
    return await journal_service.start_work_session(task)
```

**Prompts:**

```python
@mcp.prompt()
async def morning_briefing_prompt() -> str:
    """Generate morning briefing."""
    journal_service = await get_journal_service()
    return await journal_service.get_morning_briefing()
```

**Resources:**

```python
@mcp.resource("memory://journal/{date}")
async def get_journal(date: str) -> str:
    """Get journal for specific date."""
    # Implementation
```

---

## Adding a New Field

### Step 1: Update Pydantic Model

```python
# src/models/journal.py
class WorkSession(BaseModel):
    # ... existing fields ...
    mood: str = Field(default="", max_length=50)
    focus_level: int = Field(default=0, ge=0, le=5)
```

### Step 2: Create Migration

```bash
# Generate migration
alembic revision -m "add_mood_and_focus"
```

```python
# migrations/versions/004_add_mood_and_focus.py
def upgrade():
    op.add_column('work_sessions',
        sa.Column('mood', sa.String(50), default=''))
    op.add_column('work_sessions',
        sa.Column('focus_level', sa.Integer, default=0))

def downgrade():
    op.drop_column('work_sessions', 'mood')
    op.drop_column('work_sessions', 'focus_level')
```

### Step 3: Update Repository

```python
# src/storage/repositories.py
class JournalRepository:
    async def update_session(self, session: WorkSession):
        # Existing code will handle new fields automatically
        # due to SQLAlchemy reflection
        pass
```

### Step 4: Update Service

```python
# src/services/journal_service.py
async def end_work_session(
    self,
    what_i_learned: list[str] | None = None,
    challenges_faced: list[str] | None = None,
    quick_note: str = "",
    mood: str = "",  # New parameter
    focus_level: int = 0  # New parameter
) -> dict[str, Any]:
    # ... existing logic ...
    active_session.mood = mood
    active_session.focus_level = focus_level
    # ... save ...
```

### Step 5: Update MCP Tool

```python
# src/server.py
@mcp.tool()
async def end_work_session(
    what_i_learned: list[str] | None = None,
    challenges_faced: list[str] | None = None,
    quick_note: str = "",
    mood: str = "",  # New parameter
    focus_level: int = 0  # New parameter
) -> dict[str, Any]:
    journal_service = await get_journal_service()
    return await journal_service.end_work_session(
        what_i_learned,
        challenges_faced,
        quick_note,
        mood,
        focus_level
    )
```

### Step 6: Run Migration

```bash
alembic upgrade head
```

### Step 7: Add Tests

```python
# tests/unit/test_journal_models.py
def test_work_session_with_mood():
    session = WorkSession(
        task="Test",
        start_time=datetime.now(timezone.utc),
        mood="focused",
        focus_level=5
    )
    assert session.mood == "focused"
    assert session.focus_level == 5
```

---

## Adding a New Tool

### Step 1: Define Tool

```python
# src/server.py
@mcp.tool()
async def set_energy_level(level: int) -> dict[str, Any]:
    """Set energy level for today (1-5 scale)."""
    if not 1 <= level <= 5:
        return {
            "success": False,
            "error": "Energy level must be between 1 and 5"
        }

    journal_service = await get_journal_service()
    result = await journal_service.set_energy_level(level)

    return {
        "success": True,
        "level": level,
        "message": f"Energy level set to {level}/5"
    }
```

### Step 2: Implement Service Method

```python
# src/services/journal_service.py
async def set_energy_level(self, level: int) -> dict[str, Any]:
    async with self.database.session() as session:
        repo = JournalRepository(session)
        journal = await repo.get_or_create_today()
        journal.energy_level = level
        await repo.save(journal)

    return {"level": level}
```

### Step 3: Add Tests

```python
# tests/unit/test_journal_service.py
@pytest.mark.asyncio
async def test_set_energy_level(mock_database):
    service = JournalService(mock_database, None, None, None)
    result = await service.set_energy_level(4)
    assert result["level"] == 4
```

### Step 4: Document

Add to API reference documentation.

---

## Testing Extensions

### Unit Tests

```python
# tests/unit/test_custom.py
import pytest
from src.models.journal import WorkSession
from datetime import datetime, timezone

def test_custom_feature():
    """Test custom functionality."""
    session = WorkSession(
        task="Custom test",
        start_time=datetime.now(timezone.utc)
    )
    # Your assertions
    assert session.task == "Custom test"
```

### Integration Tests

```python
# tests/integration/test_custom_integration.py
import pytest
from src.storage.database import Database
from src.services.journal_service import JournalService

@pytest.mark.asyncio
async def test_custom_integration(test_database):
    """Test with real database."""
    service = JournalService(test_database, None, None, None)
    # Your test logic
```

### Run Tests

```bash
# Unit tests
pytest tests/unit/test_custom.py -v

# Integration tests
pytest tests/integration/test_custom_integration.py -v

# All tests
pytest tests/ -v
```

---

## Configuration Management

### Adding Configuration Option

**Step 1: Update Config Model**

```python
# src/utils/config.py
class JournalConfig(BaseModel):
    enabled: bool = True
    auto_reflection: bool = True
    min_session_minutes: int = 30
    custom_option: str = "default"  # New option
```

**Step 2: Update config.yaml**

```yaml
personal:
  journal:
    enabled: true
    auto_reflection: true
    min_session_minutes: 30
    custom_option: "value"
```

**Step 3: Use in Code**

```python
settings = get_settings()
custom_value = settings.personal.journal.custom_option
```

---

## Performance Optimization

### Database Queries

**Use connection pooling:**

```python
# src/storage/database.py
engine = create_async_engine(
    database_url,
    pool_size=10,
    max_overflow=20
)
```

**Batch operations:**

```python
# Instead of multiple queries
async with database.session() as session:
    for item in items:
        await repo.save(item)  # N queries

# Use bulk operations
async with database.session() as session:
    await repo.bulk_save(items)  # 1 query
```

### Vector Store

**Batch embeddings:**

```python
# Instead of one at a time
for memory in memories:
    await vector_store.add_memory(memory)  # N API calls

# Batch them
await vector_store.add_memories_batch(memories)  # 1 API call
```

**Cache frequently accessed:**

```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_recent_reflections():
    # Expensive query
    pass
```

---

## Error Handling

### Standard Error Response

```python
def error_response(error_msg: str, tip: str = "") -> dict[str, Any]:
    """Standard error response format."""
    return {
        "success": False,
        "error": error_msg,
        "tip": tip
    }
```

### Try-Catch Pattern

```python
async def safe_operation():
    """Wrap operations in try-catch."""
    try:
        # Your logic
        result = await risky_operation()
        return {"success": True, "result": result}
    except ValueError as e:
        return error_response(f"Invalid input: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return error_response("Operation failed", "Check logs")
```

---

## Logging

### Setup Logger

```python
# src/utils/logger.py
import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
```

### Use Logger

```python
# In your module
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def some_operation():
    logger.info("Starting operation")
    try:
        # Logic
        logger.debug("Details...")
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
```

---

## Code Style

### Type Hints

```python
# Always use type hints
async def process_session(
    session: WorkSession,
    generate_reflection: bool = True
) -> dict[str, Any]:
    ...
```

### Docstrings

```python
async def complex_function(param1: str, param2: int) -> dict:
    """Brief description of what it does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary containing results

    Raises:
        ValueError: If param2 is negative
    """
    ...
```

### Formatting

```bash
# Use black for formatting
black src/ tests/

# Use isort for imports
isort src/ tests/

# Use mypy for type checking
mypy src/
```

---

## Debugging

### Enable Debug Mode

```yaml
# config.yaml
server:
  log_level: "DEBUG"
```

### Use Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use breakpoint() (Python 3.7+)
breakpoint()
```

### Debug Async Code

```python
# Use asyncio debug mode
import asyncio
asyncio.run(main(), debug=True)
```

---

## Deployment

### Production Checklist

- [ ] Set `log_level: "INFO"` in config
- [ ] Enable connection pooling
- [ ] Set up log rotation
- [ ] Configure retention policy
- [ ] Enable auto-cleanup
- [ ] Test with production data volume
- [ ] Monitor memory usage
- [ ] Set up health checks

### Environment Variables

```bash
export MEMORY_SERVER__PERSONAL__JOURNAL__ENABLED=true
export MEMORY_SERVER__SERVER__LOG_LEVEL=INFO
export MEMORY_SERVER__STORAGE__SQLITE__DATABASE_URL=sqlite+aiosqlite:///prod.db
```

---

## Resources

### Key Files

- `src/models/journal.py` - Data models
- `src/storage/repositories.py` - Database access
- `src/services/journal_service.py` - Business logic
- `src/server.py` - MCP interface
- `tests/` - Test suite

### External Dependencies

- FastMCP - MCP server framework
- SQLAlchemy - ORM
- Pydantic - Data validation
- ChromaDB - Vector store
- Alembic - Migrations

### Documentation

- [FastMCP Docs](https://github.com/jlowin/fastmcp)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Pydantic](https://docs.pydantic.dev/)
- [ChromaDB](https://docs.trychroma.com/)

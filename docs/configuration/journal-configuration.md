# Daily Journal - Configuration Reference

## Complete Configuration Options

```yaml
personal:
  journal:
    # Enable journal feature
    enabled: true

    # Auto-generate AI reflections
    auto_reflection: true

    # Min session minutes for reflection
    # Range: 1-1440
    # Default: 30
    min_session_minutes: 30

    # Max tokens for reflection
    # Range: 50-500
    # Default: 150
    reflection_length: 150

    # Max tokens for daily summary
    # Range: 100-1000
    # Default: 200
    summary_length: 200

storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./data/memory.db"
    echo: false
    pool_size: 5

  chroma:
    persist_directory: "./data/chroma_db"
    embedding_model: "all-MiniLM-L6-v2"
    collection_name: "memory_embeddings"

server:
  log_level: "INFO"
  log_format: "text"
  log_file: null

retention:
  days: 365
  auto_cleanup: false
  archive_old: true

performance:
  cache_enabled: true
  cache_ttl: 300
  embedding_batch_size: 32
```

---

## Configuration Details

### Journal Settings

#### `enabled`

- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable/disable journal feature globally

```yaml
personal:
  journal:
    enabled: false # Disable journal
```

#### `auto_reflection`

- **Type:** `boolean`
- **Default:** `true`
- **Description:** Automatically generate AI reflections for sessions

```yaml
personal:
  journal:
    auto_reflection: false # Disable auto-reflection
```

#### `min_session_minutes`

- **Type:** `integer`
- **Range:** `1-1440` (1 minute to 24 hours)
- **Default:** `30`
- **Description:** Minimum session length to trigger reflection

```yaml
personal:
  journal:
    min_session_minutes: 45 # Reflection for 45+ min sessions
```

#### `reflection_length`

- **Type:** `integer`
- **Range:** `50-500`
- **Default:** `150`
- **Description:** Maximum tokens for session reflection

```yaml
personal:
  journal:
    reflection_length: 200 # Longer reflections
```

#### `summary_length`

- **Type:** `integer`
- **Range:** `100-1000`
- **Default:** `200`
- **Description:** Maximum tokens for daily summary

```yaml
personal:
  journal:
    summary_length: 300 # More detailed summaries
```

---

### Storage Settings

#### SQLite

**`database_url`**

- **Type:** `string`
- **Default:** `"sqlite+aiosqlite:///./data/memory.db"`
- **Description:** Database connection URL

```yaml
storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./custom_path.db"
```

**`echo`**

- **Type:** `boolean`
- **Default:** `false`
- **Description:** Log all SQL queries (debug only)

```yaml
storage:
  sqlite:
    echo: true # Enable SQL logging
```

**`pool_size`**

- **Type:** `integer`
- **Default:** `5`
- **Description:** Connection pool size

```yaml
storage:
  sqlite:
    pool_size: 10 # More concurrent connections
```

#### ChromaDB

**`persist_directory`**

- **Type:** `string`
- **Default:** `"./data/chroma_db"`
- **Description:** ChromaDB data directory

```yaml
storage:
  chroma:
    persist_directory: "/var/lib/chroma_db"
```

**`embedding_model`**

- **Type:** `string`
- **Default:** `"all-MiniLM-L6-v2"`
- **Description:** Sentence transformer model name

```yaml
storage:
  chroma:
    embedding_model: "all-mpnet-base-v2" # Better quality
```

**`collection_name`**

- **Type:** `string`
- **Default:** `"memory_embeddings"`
- **Description:** ChromaDB collection name

```yaml
storage:
  chroma:
    collection_name: "journal_memories"
```

---

### Server Settings

#### `log_level`

- **Type:** `string`
- **Values:** `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`
- **Default:** `"INFO"`
- **Description:** Logging verbosity

```yaml
server:
  log_level: "DEBUG" # Verbose logging
```

#### `log_format`

- **Type:** `string`
- **Values:** `"text"`, `"json"`
- **Default:** `"text"`
- **Description:** Log output format

```yaml
server:
  log_format: "json" # Structured logging
```

#### `log_file`

- **Type:** `string | null`
- **Default:** `null`
- **Description:** Log file path (null = stdout)

```yaml
server:
  log_file: "./logs/memory-server.log"
```

---

### Retention Settings

#### `days`

- **Type:** `integer`
- **Default:** `365`
- **Description:** Days to retain journal data

```yaml
retention:
  days: 90 # Keep 90 days
```

#### `auto_cleanup`

- **Type:** `boolean`
- **Default:** `false`
- **Description:** Automatically delete old data

```yaml
retention:
  auto_cleanup: true # Enable auto-cleanup
```

#### `archive_old`

- **Type:** `boolean`
- **Default:** `true`
- **Description:** Archive data before deletion

```yaml
retention:
  archive_old: false # Don't archive
```

---

### Performance Settings

#### `cache_enabled`

- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable in-memory caching

```yaml
performance:
  cache_enabled: false # Disable cache
```

#### `cache_ttl`

- **Type:** `integer`
- **Default:** `300`
- **Description:** Cache TTL in seconds

```yaml
performance:
  cache_ttl: 600 # 10 minute cache
```

#### `embedding_batch_size`

- **Type:** `integer`
- **Default:** `32`
- **Description:** Batch size for embeddings

```yaml
performance:
  embedding_batch_size: 64 # Larger batches
```

---

## Environment Variable Overrides

Configuration can be overridden with environment variables using double underscores:

```bash
# Format: MEMORY_SERVER__SECTION__SUBSECTION__KEY=value

# Journal settings
export MEMORY_SERVER__PERSONAL__JOURNAL__ENABLED=true
export MEMORY_SERVER__PERSONAL__JOURNAL__MIN_SESSION_MINUTES=45
export MEMORY_SERVER__PERSONAL__JOURNAL__AUTO_REFLECTION=false

# Storage settings
export MEMORY_SERVER__STORAGE__SQLITE__DATABASE_URL="sqlite+aiosqlite:///./prod.db"
export MEMORY_SERVER__STORAGE__CHROMA__PERSIST_DIRECTORY="/var/lib/chroma"

# Server settings
export MEMORY_SERVER__SERVER__LOG_LEVEL=INFO
export MEMORY_SERVER__SERVER__LOG_FILE="./logs/server.log"
```

**Priority:** Environment variables > config.yaml > defaults

---

## Configuration Profiles

### Development

```yaml
# config.dev.yaml
personal:
  journal:
    min_session_minutes: 5 # Lower for testing
    reflection_length: 100
    summary_length: 150

storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./data/dev.db"
    echo: true # Log SQL queries

server:
  log_level: "DEBUG"
  log_format: "text"

performance:
  cache_enabled: false # Disable for debugging
```

**Usage:**

```bash
export CONFIG_FILE=config.dev.yaml
python -m src.server
```

---

### Production

```yaml
# config.prod.yaml
personal:
  journal:
    min_session_minutes: 30
    reflection_length: 150
    summary_length: 200

storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./data/prod.db"
    echo: false
    pool_size: 10

  chroma:
    persist_directory: "/var/lib/chroma_db"

server:
  log_level: "INFO"
  log_format: "json"
  log_file: "/var/log/memory-server/server.log"

retention:
  days: 365
  auto_cleanup: true
  archive_old: true

performance:
  cache_enabled: true
  cache_ttl: 600
  embedding_batch_size: 64
```

**Usage:**

```bash
export CONFIG_FILE=config.prod.yaml
python -m src.server
```

---

### Testing

```yaml
# config.test.yaml
personal:
  journal:
    min_session_minutes: 1 # Accept any duration
    auto_reflection: false # Disable for speed

storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./data/test.db"

  chroma:
    persist_directory: "./data/test_chroma"

server:
  log_level: "WARNING" # Quiet tests

performance:
  cache_enabled: false
```

**Usage:**

```bash
export CONFIG_FILE=config.test.yaml
pytest tests/
```

---

## Configuration Validation

### Validate Configuration

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Validate against schema
python scripts/validate_config.py
```

### Validation Script

```python
# scripts/validate_config.py
from src.utils.config import get_settings

try:
    settings = get_settings()
    print("✅ Configuration valid")
    print(f"Journal enabled: {settings.personal.journal.enabled}")
    print(f"Min session: {settings.personal.journal.min_session_minutes}min")
    print(f"Database: {settings.storage.sqlite.database_url}")
except Exception as e:
    print(f"❌ Configuration invalid: {e}")
    exit(1)
```

---

## Common Configurations

### Minimal (Fast, No AI)

```yaml
personal:
  journal:
    enabled: true
    auto_reflection: false # No AI

storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./data/memory.db"

  chroma:
    persist_directory: "./data/chroma_db"

server:
  log_level: "INFO"
```

---

### High Performance

```yaml
personal:
  journal:
    enabled: true
    auto_reflection: true
    min_session_minutes: 30

storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./data/memory.db"
    pool_size: 20
    max_overflow: 40

  chroma:
    persist_directory: "./data/chroma_db"

server:
  log_level: "WARNING"

performance:
  cache_enabled: true
  cache_ttl: 900 # 15 minutes
  embedding_batch_size: 128
```

---

### Privacy Focused

```yaml
personal:
  journal:
    enabled: true
    auto_reflection: false # No external API calls

storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./data/memory.db"

  chroma:
    persist_directory: "./data/chroma_db"
    embedding_model: "all-MiniLM-L6-v2" # Local model

server:
  log_level: "ERROR" # Minimal logging

retention:
  days: 30 # Short retention
  auto_cleanup: true
```

---

## Troubleshooting Configuration

### Config Not Loading

**Check:**

1. File exists at expected path
2. YAML syntax is valid
3. Environment variables set correctly

```bash
# Check file
ls -la config.yaml

# Validate YAML
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

# Check env vars
env | grep MEMORY_SERVER
```

---

### Changes Not Applied

**Restart required:**

```bash
# Configuration loads at startup
# Stop and restart server
```

---

### Invalid Values

**Check logs:**

```bash
tail -100 logs/memory-server.log | grep "config"
```

**Common issues:**

- Integer out of range
- Invalid path
- Unknown enum value
- Missing required field

# MCP Memory Server

Production-ready MCP (Model Context Protocol) server for LLM memory management with semantic search capabilities.

## ✨ Features

- 🧠 **Hierarchical Memory** - Project briefs, decisions, tasks, and context
- 🔍 **Semantic Search** - ChromaDB-powered vector search with local embeddings
- 📝 **Decision Logging** - ADR-style architectural decision records
- ✅ **Task Tracking** - Progress tracking with status grouping
- 🔄 **Dual Transport** - STDIO for local clients, HTTP for remote access
- � **Security** - Bearer token authentication for HTTP, CORS protection, rate limiting
- 🗃️ **Database Migrations** - Alembic-powered schema management
- 🔁 **Retry Logic** - Resilient vector store operations with exponential backoff
- ✅ **Type-Safe** - Full Pydantic validation with input size limits
- 🐳 **Docker Ready** - Multi-stage build with pre-downloaded embeddings

## 🚀 Quick Start

### Local Development (STDIO)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run server (STDIO transport)
python -m src.server
```

### HTTP Transport with Authentication

```bash
# Set API key for authentication (optional - if not set, all requests allowed)
export MCP_API_KEY="your-secure-api-key-here"

# Configure CORS (comma-separated origins)
export MEMORY_SERVER__TRANSPORT__HTTP__CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Run HTTP server
python -m src.server --transport http --port 8080
```

**Authentication**: When `MCP_API_KEY` is set, all HTTP requests require `Authorization: Bearer <token>` header.

### Docker

```bash
# Build and run with environment variables
docker-compose up -d

# Check health
curl http://localhost:8080/health

# With authentication
curl -H "Authorization: Bearer your-api-key" http://localhost:8080/health
```

## 📦 MCP Resources

All resources return standardized responses with error handling.

| Resource URI                  | Description             |
| ----------------------------- | ----------------------- |
| `memory://project/brief`      | Project overview        |
| `memory://project/tech-stack` | Technology stack        |
| `memory://context/active`     | Current working context |
| `memory://decisions`          | All decisions           |
| `memory://decisions/{id}`     | Specific decision       |
| `memory://progress`           | Tasks by status         |
| `memory://tasks`              | All tasks               |
| `memory://tasks/{id}`         | Specific task           |

## 🔧 MCP Tools

All tools return `{"success": bool, "data": Any, "error": str | None}` format.

| Tool                    | Description                |
| ----------------------- | -------------------------- |
| `set_project_brief`     | Set/update project info    |
| `set_tech_stack`        | Set/update technologies    |
| `update_active_context` | Update working context     |
| `log_decision`          | Log architectural decision |
| `create_task`           | Create new task            |
| `update_task_status`    | Update task status         |
| `search_memory`         | Semantic search            |
| `add_memory_note`       | Add free-form note         |

## 💬 MCP Prompts

| Prompt                    | Description               |
| ------------------------- | ------------------------- |
| `context_prompt`          | Current context injection |
| `recent_decisions_prompt` | Recent decisions          |
| `progress_summary_prompt` | Progress overview         |
| `full_context_prompt`     | Complete context          |

## ⚙️ Configuration

Create `config.yaml`:

```yaml
server:
  name: "memory-server"
  log_level: "INFO"

storage:
  sqlite:
    database_url: "sqlite+aiosqlite:///./data/memory.db"
  chroma:
    persist_directory: "./data/chroma_db"
    embedding_model: "all-MiniLM-L6-v2"

transport:
  default: "stdio"
  http:
    port: 8080
    cors_origins: [] # Empty by default for security

memory:
  retention_days: 90
  max_decisions: 1000
  max_tasks: 500
```

### Environment Variables

All configuration can be overridden with environment variables:

```bash
# API Authentication (optional)
export MCP_API_KEY="your-secure-token"

# CORS Configuration
export MEMORY_SERVER__TRANSPORT__HTTP__CORS_ORIGINS="https://example.com"

# Database URL
export MEMORY_SERVER__STORAGE__SQLITE__DATABASE_URL="sqlite+aiosqlite:///./data/memory.db"

# Chroma DB Path
export MEMORY_SERVER__STORAGE__CHROMA__PERSIST_DIRECTORY="./data/chroma_db"
```

## 🗃️ Database Migrations

The server uses Alembic for database schema management:

```bash
# Initialize database (run migrations)
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history
```

## 🔒 Security Features

### HTTP Authentication

When `MCP_API_KEY` environment variable is set, all HTTP requests require bearer token:

```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8080/...
```

STDIO transport remains unauthenticated for local development use.

### CORS Protection

Default CORS configuration is empty (no origins allowed). Configure specific origins:

```yaml
# config.yaml
transport:
  http:
    cors_origins: ["https://yourdomain.com"]
```

⚠️ **Warning**: Using wildcard `["*"]` allows all origins - insecure for production.

### Rate Limiting

HTTP endpoints are rate-limited to 100 requests per minute per IP by default. Returns HTTP 429 when exceeded.

### Input Validation

All inputs have size limits to prevent DoS attacks:

- Titles: 500 characters
- Descriptions: 5,000 characters
- Content fields: 50,000 characters
- Lists: 50-100 items max
- Tags: 50 items, 100 characters each

## 🔌 Client Configuration

### Claude Desktop

```json
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/mcp-memory-server"
    }
  }
}
```

### VSCode / Cursor

```json
{
  "mcp.servers": {
    "memory": {
      "command": "python",
      "args": ["-m", "src.server", "--transport", "stdio"]
    }
  }
}
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/unit/
pytest tests/integration/
```

## 📁 Project Structure

```
mcp-memory-server/
├── src/
│   ├── server.py          # FastMCP server
│   ├── models/            # Pydantic models with validation
│   ├── storage/           # Database & vector store
│   ├── services/          # Business logic with retry
│   ├── middleware/        # Auth & rate limiting
│   └── utils/             # Config & logging
├── migrations/            # Alembic database migrations
│   └── versions/
├── tests/
├── config.yaml
├── alembic.ini
├── requirements.txt       # Core dependencies
├── requirements.lock      # Locked versions
├── Dockerfile
└── docker-compose.yml
```

## 🏗️ Architecture Improvements

### Completed Enhancements

#### Priority 1: Critical Security & Stability

✅ **HTTP Authentication** - Bearer token authentication via `MCP_API_KEY`  
✅ **Database Migrations** - Alembic for schema management  
✅ **Error Handling** - Standardized responses for all tools/resources  
✅ **CORS Security** - Default empty origins, configurable via env vars

#### Priority 2: Important Improvements

✅ **Dependency Injection** - ServiceManager for proper lifecycle  
✅ **Vector Store Retry** - 3 retries with exponential backoff  
✅ **Timezone Consistency** - All timestamps use UTC  
✅ **Input Validation** - Size limits on all fields  
✅ **Race Condition Fix** - Optimistic locking for ActiveContext  
✅ **Docker Optimization** - Pre-downloaded embedding model

#### Priority 3: Enhancements

✅ **Rate Limiting** - 100 req/min per IP for HTTP  
✅ **Python Health Check** - No curl dependency  
✅ **Dependency Locking** - requirements.lock file

## 📄 License

MIT License

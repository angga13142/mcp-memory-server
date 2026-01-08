# MCP Memory Server

Production-ready MCP (Model Context Protocol) server for LLM memory management with semantic search capabilities.

## ✨ Features

- 🧠 **Hierarchical Memory** - Project briefs, decisions, tasks, and context
- 🔍 **Semantic Search** - ChromaDB-powered vector search with local embeddings
- 📝 **Decision Logging** - ADR-style architectural decision records
- ✅ **Task Tracking** - Progress tracking with status grouping
- 🔄 **Dual Transport** - STDIO for local clients, HTTP for remote access
- 🐳 **Docker Ready** - Multi-stage build with health checks
- ✅ **Type-Safe** - Full Pydantic validation and type hints

## 🚀 Quick Start

### Local Development (STDIO)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server (STDIO transport)
python -m src.server
```

### HTTP Transport

```bash
python -m src.server --transport http --port 8080
```

### Docker

```bash
# Build and run
docker-compose up -d

# Check health
curl http://localhost:8080/health
```

## 📦 MCP Resources

| Resource URI | Description |
|--------------|-------------|
| `memory://project/brief` | Project overview |
| `memory://project/tech-stack` | Technology stack |
| `memory://context/active` | Current working context |
| `memory://decisions` | All decisions |
| `memory://decisions/{id}` | Specific decision |
| `memory://progress` | Tasks by status |
| `memory://tasks` | All tasks |
| `memory://tasks/{id}` | Specific task |

## 🔧 MCP Tools

| Tool | Description |
|------|-------------|
| `set_project_brief` | Set/update project info |
| `set_tech_stack` | Set/update technologies |
| `update_active_context` | Update working context |
| `log_decision` | Log architectural decision |
| `create_task` | Create new task |
| `update_task_status` | Update task status |
| `search_memory` | Semantic search |
| `add_memory_note` | Add free-form note |

## 💬 MCP Prompts

| Prompt | Description |
|--------|-------------|
| `context_prompt` | Current context injection |
| `recent_decisions_prompt` | Recent decisions |
| `progress_summary_prompt` | Progress overview |
| `full_context_prompt` | Complete context |

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
```

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
│   ├── models/            # Pydantic models
│   ├── storage/           # Database & vector store
│   ├── services/          # Business logic
│   └── utils/             # Config & logging
├── tests/
├── config.yaml
├── Dockerfile
└── docker-compose.yml
```

## 📄 License

MIT License

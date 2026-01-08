#!/bin/bash
set -e

echo "🚀 MCP Memory Server - Starting..."
echo "=================================="

wait_for_dependency() {
    local host=$1
    local port=$2
    local service=$3
    
    echo "⏳ Waiting for $service ($host:$port)..."
    
    timeout 60 bash -c "
        until python -c \"import socket; s=socket.socket(); s.settimeout(1); s.connect(('$host', $port)); s.close();\" 2>/dev/null; do
            echo '   Still waiting for $service...'
            sleep 2
        done
    "
    
    if [ $? -eq 0 ]; then
        echo "✅ $service is ready"
    else
        echo "❌ Timeout waiting for $service"
        exit 1
    fi
}

if [ ! -z "$REDIS_HOST" ]; then
    wait_for_dependency "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}" "Redis"
fi

echo "📁 Ensuring data directories exist..."
mkdir -p /app/data/chroma_db /app/logs
echo "✅ Data directories ready"

echo "🔄 Running database migrations..."
if alembic upgrade head; then
    echo "✅ Database migrations completed"
else
    echo "❌ Database migration failed"
    exit 1
fi

echo "🔍 Verifying database schema..."
python -c "
import asyncio
from src.storage.database import Database
from src.utils.config import get_settings

async def verify():
    db = Database(get_settings())
    await db.init()
    async with db.session() as session:
        from sqlalchemy import text
        result = await session.execute(text('SELECT name FROM sqlite_master WHERE type=\"table\"'))
        tables = [row[0] for row in result.fetchall()]
        print(f'   Tables found: {len(tables)}')
        required = ['daily_journals', 'work_sessions', 'session_reflections']
        for table in required:
            if table in tables:
                print(f'   ✅ {table}')
            else:
                print(f'   ❌ Missing table: {table}')
                exit(1)
    await db.close()

asyncio.run(verify())
"

if [ $? -ne 0 ]; then
    echo "❌ Database verification failed"
    exit 1
fi

echo "✅ Database schema verified"

echo "🔥 Pre-warming embedding model..."
python -c "
from sentence_transformers import SentenceTransformer
import time

start = time.time()
model = SentenceTransformer('all-MiniLM-L6-v2')
_ = model.encode('warmup')
elapsed = time.time() - start

print(f'   Model loaded in {elapsed:.2f}s')
" 

echo "✅ Embedding model ready"

echo "⚙️  Configuration:"
echo "   Environment: ${ENVIRONMENT:-production}"
echo "   Log Level: ${LOG_LEVEL:-INFO}"
echo "   Database: ${MEMORY_SERVER__STORAGE__SQLITE__DATABASE_URL:-sqlite+aiosqlite:///./data/memory.db}"
echo "   Journal Enabled: ${MEMORY_SERVER__PERSONAL__JOURNAL__ENABLED:-true}"
echo ""

echo "🎯 Starting application..."
echo "=================================="
exec "$@"

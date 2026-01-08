#!/usr/bin/env python3
"""Health check script for Docker container."""

import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def check_database():
    """Check database connectivity."""
    try:
        from src.storage.database import Database
        from src.utils.config import get_settings
        
        settings = get_settings()
        database = Database(settings)
        await database.init()
        
        async with database.session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        await database.close()
        return True
    except Exception as e:
        print(f"Database check failed: {e}", file=sys.stderr)
        return False


async def check_vector_store():
    """Check vector store availability."""
    try:
        from src.storage.vector_store import VectorMemoryStore
        from src.utils.config import get_settings
        
        settings = get_settings()
        vector_store = VectorMemoryStore(settings)
        await vector_store.init()
        
        count = await vector_store.count()
        
        return True
    except Exception as e:
        print(f"Vector store check failed: {e}", file=sys.stderr)
        return False


async def check_embedding_model():
    """Check embedding model is loaded."""
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_embedding = model.encode("health check")
        
        assert len(test_embedding) == 384
        
        return True
    except Exception as e:
        print(f"Embedding model check failed: {e}", file=sys.stderr)
        return False


async def check_data_directories():
    """Check required directories exist and are writable."""
    try:
        data_dir = Path("./data")
        logs_dir = Path("./logs")
        
        assert data_dir.exists(), "Data directory missing"
        assert logs_dir.exists(), "Logs directory missing"
        
        test_file = data_dir / ".health_check"
        test_file.write_text("ok")
        test_file.unlink()
        
        return True
    except Exception as e:
        print(f"Directory check failed: {e}", file=sys.stderr)
        return False


async def health_check():
    """Perform comprehensive health check."""
    checks = {
        "database": check_database,
        "vector_store": check_vector_store,
        "embedding_model": check_embedding_model,
        "directories": check_data_directories,
    }
    
    results = {}
    for name, check_func in checks.items():
        try:
            results[name] = await check_func()
        except Exception as e:
            print(f"Check {name} crashed: {e}", file=sys.stderr)
            results[name] = False
    
    all_passed = all(results.values())
    
    if not all_passed:
        print("Health check FAILED:", file=sys.stderr)
        for name, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {name}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(health_check())
    sys.exit(exit_code)

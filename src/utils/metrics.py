"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from functools import wraps
import time
from datetime import datetime, timezone


app_info = Info('mcp_memory_server', 'Application information')
app_info.info({'version': '1.0.0', 'feature': 'daily_journal', 'python_version': '3.11'})


# Journal Metrics
journal_sessions_total = Counter('mcp_journal_sessions_total', 'Total work sessions started', ['status'])
journal_sessions_active = Gauge('mcp_journal_sessions_active', 'Currently active work sessions')
journal_session_duration = Histogram('mcp_journal_session_duration_minutes', 'Session duration in minutes', buckets=[5, 15, 30, 60, 120, 240, 480])
journal_reflections_generated = Counter('mcp_journal_reflections_generated_total', 'AI reflections generated', ['status'])
journal_reflection_generation_time = Histogram('mcp_journal_reflection_generation_seconds', 'Reflection generation time', buckets=[0.5, 1, 2, 5, 10, 30])
journal_daily_summaries = Counter('mcp_journal_daily_summaries_total', 'Daily summaries generated', ['status'])
journal_daily_summary_time = Histogram('mcp_journal_daily_summary_seconds', 'Daily summary generation time', buckets=[1, 2, 5, 10, 30])
journal_learnings_captured = Counter('mcp_journal_learnings_captured_total', 'Learnings captured')
journal_challenges_noted = Counter('mcp_journal_challenges_noted_total', 'Challenges noted')
journal_wins_captured = Counter('mcp_journal_wins_captured_total', 'Wins captured')


# Database Metrics
db_connections_active = Gauge('mcp_db_connections_active', 'Active database connections')
db_connections_total = Counter('mcp_db_connections_total', 'Total database connections', ['status'])
db_query_duration = Histogram('mcp_db_query_duration_seconds', 'Database query duration', ['operation'], buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0])
db_queries_total = Counter('mcp_db_queries_total', 'Total database queries', ['operation', 'status'])


# Vector Store Metrics
vector_embeddings_generated = Counter('mcp_vector_embeddings_generated_total', 'Embeddings generated', ['status'])
vector_embedding_time = Histogram('mcp_vector_embedding_seconds', 'Embedding generation time', buckets=[0.1, 0.5, 1, 2, 5, 10])
vector_searches_total = Counter('mcp_vector_searches_total', 'Vector searches', ['status'])
vector_search_time = Histogram('mcp_vector_search_seconds', 'Vector search time', buckets=[0.01, 0.05, 0.1, 0.5, 1, 2])
vector_store_size = Gauge('mcp_vector_store_size_bytes', 'Vector store size in bytes')
vector_memory_count = Gauge('mcp_vector_memory_count', 'Memories in vector store')


# API Metrics
api_requests_total = Counter('mcp_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
api_request_duration = Histogram('mcp_api_request_duration_seconds', 'API request duration', ['method', 'endpoint'], buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5])
api_errors_total = Counter('mcp_api_errors_total', 'API errors', ['endpoint', 'error_type'])


# System Metrics
system_memory_usage = Gauge('mcp_system_memory_usage_bytes', 'Memory usage in bytes')
system_cpu_usage = Gauge('mcp_system_cpu_usage_percent', 'CPU usage percentage')


def track_session_operation(func):
    """Decorator to track session operations."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            if result.get('success'):
                journal_sessions_total.labels(status='success').inc()
            else:
                journal_sessions_total.labels(status='failed').inc()
            return result
        except Exception as e:
            journal_sessions_total.labels(status='failed').inc()
            raise
    return wrapper


def track_reflection_generation(func):
    """Decorator to track reflection generation."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            journal_reflection_generation_time.observe(duration)
            journal_reflections_generated.labels(status='success').inc()
            return result
        except Exception as e:
            journal_reflections_generated.labels(status='failed').inc()
            raise
    return wrapper


def track_db_query(operation: str):
    """Decorator to track database queries."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                db_query_duration.labels(operation=operation).observe(duration)
                db_queries_total.labels(operation=operation, status='success').inc()
                return result
            except Exception as e:
                db_queries_total.labels(operation=operation, status='failed').inc()
                raise
        return wrapper
    return decorator


def track_vector_operation(operation: str):
    """Decorator to track vector store operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                if operation == 'embed':
                    vector_embedding_time.observe(duration)
                    vector_embeddings_generated.labels(status='success').inc()
                elif operation == 'search':
                    vector_search_time.observe(duration)
                    vector_searches_total.labels(status='success').inc()
                return result
            except Exception as e:
                if operation == 'embed':
                    vector_embeddings_generated.labels(status='failed').inc()
                elif operation == 'search':
                    vector_searches_total.labels(status='failed').inc()
                raise
        return wrapper
    return decorator


async def update_system_metrics():
    """Update system metrics."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.used)
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage.set(cpu_percent)
    except ImportError:
        pass


async def update_vector_store_metrics(vector_store):
    """Update vector store metrics."""
    try:
        count = await vector_store.count()
        vector_memory_count.set(count)
        from pathlib import Path
        persist_dir = Path(vector_store.persist_directory)
        if persist_dir.exists():
            total_size = sum(f.stat().st_size for f in persist_dir.rglob('*') if f.is_file())
            vector_store_size.set(total_size)
    except Exception as e:
        print(f"Failed to update vector store metrics: {e}")


def get_metrics():
    """Get current metrics in Prometheus format."""
    return generate_latest(REGISTRY)

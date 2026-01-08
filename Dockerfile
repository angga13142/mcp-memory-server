# syntax=docker/dockerfile:1

# =============================================================================
# MCP Memory Server Dockerfile
# Multi-stage build for production-optimized container
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Pre-download embedding model during build
RUN pip install sentence-transformers && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Install runtime dependencies (removed curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Set model cache directory and copy pre-downloaded model from builder
ENV TRANSFORMERS_CACHE=/app/.cache
COPY --from=builder /root/.cache /app/.cache

# Copy application code
COPY src/ ./src/
COPY config.yaml .
COPY alembic.ini .
COPY migrations/ ./migrations/

# Create data directories
RUN mkdir -p /app/data/sqlite /app/data/chroma_db \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MEMORY_SERVER__STORAGE__SQLITE__DATABASE_URL="sqlite+aiosqlite:///./data/sqlite/memory.db" \
    MEMORY_SERVER__STORAGE__CHROMA__PERSIST_DIRECTORY="./data/chroma_db"

# Expose HTTP port
EXPOSE 8080

# Health check using Python script
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python src/health_check.py || exit 1

# Default command - HTTP transport
CMD ["python", "-m", "src.server", "--transport", "http", "--port", "8080"]

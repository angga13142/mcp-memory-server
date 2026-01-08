# =============================================================================
# Stage 1: Builder - Install dependencies and download models
# =============================================================================
FROM python:3.11-slim as builder

ARG TRANSFORMERS_CACHE=/app/.cache
ARG ENVIRONMENT=production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.lock* pyproject.toml* ./

RUN pip install --upgrade pip && \
    if [ -f requirements.lock ]; then \
    pip install -r requirements.lock; \
    else \
    pip install -r requirements.txt; \
    fi

ENV TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}
RUN mkdir -p ${TRANSFORMERS_CACHE} && \
    python -c "from sentence_transformers import SentenceTransformer; \
    model = SentenceTransformer('all-MiniLM-L6-v2'); \
    print('Model cached successfully');"

# =============================================================================
# Stage 2: Runtime - Slim production image
# =============================================================================
FROM python:3.11-slim

LABEL maintainer="your-email@example.com"
LABEL description="MCP Memory Server - Daily Work Journal"
LABEL version="1.0.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_CACHE=/app/.cache \
    PATH="/app/.venv/bin:$PATH" \
    TZ=UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-0 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 appuser && \
    mkdir -p /app /app/data /app/logs /app/.cache && \
    chown -R appuser:appuser /app

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --from=builder --chown=appuser:appuser /app/.cache /app/.cache

COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser config.yaml ./config.yaml
COPY --chown=appuser:appuser scripts/ ./scripts/

RUN chmod +x scripts/*.py scripts/*.sh 2>/dev/null || true

USER appuser

RUN mkdir -p /app/data/chroma_db /app/logs

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python scripts/health_check.py || exit 1

COPY --chown=appuser:appuser scripts/docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]

CMD ["python", "-m", "src.server"]
EXPOSE 8080

# Health check using Python script
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python src/health_check.py || exit 1

# Default command - HTTP transport
CMD ["python", "-m", "src.server", "--transport", "http", "--port", "8080"]

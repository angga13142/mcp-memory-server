#!/bin/bash
# Docker commands reference

# BUILD
docker-compose build
docker build -t mcp-memory-server:1.0.0 .
docker tag mcp-memory-server:1.0.0 mcp-memory-server:latest
docker-compose build --no-cache

# RUN
docker-compose up -d
docker-compose up
docker-compose -f docker-compose.prod.yml up -d
VERSION=1.0.0 docker-compose -f docker-compose.prod.yml up -d

# LOGS
docker-compose logs -f memory-server
docker-compose logs --tail=100 memory-server
docker-compose logs -f

# HEALTH & STATUS
docker-compose ps
docker inspect --format='{{.State.Health.Status}}' mcp-memory-dev
docker-compose exec memory-server python scripts/health_check.py

# MAINTENANCE
docker-compose down
docker-compose down -v
docker-compose restart memory-server
docker-compose restart

# DATABASE
docker-compose exec memory-server alembic upgrade head
docker-compose exec memory-server alembic current
docker-compose exec memory-server sqlite3 /app/data/memory.db
docker-compose exec memory-server cp /app/data/memory.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db

# CLEANUP
docker-compose rm -f
docker system prune -a
docker volume prune

# DEBUGGING
docker-compose exec memory-server /bin/bash
docker-compose exec memory-server python
docker stats mcp-memory-dev
docker inspect mcp-memory-dev

# PRODUCTION DEPLOYMENT
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --no-deps --build mcp-memory-server
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml exec mcp-memory-server python scripts/health_check.py

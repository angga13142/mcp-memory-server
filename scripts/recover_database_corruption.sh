#!/bin/bash
# Database corruption recovery for SQLite (mcp-memory-server)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="/var/backups/mcp-monitoring/logs/database_recovery.log"
APP_SERVICE="mcp-memory-server"
COMPOSE_FILE="$REPO_DIR/docker-compose.yml"
DB_PATH="/app/data/memory.db"

mkdir -p "$(dirname "$LOG_FILE")"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
fail() { log "❌ ERROR: $1"; exit 1; }

log "🔧 Database Corruption Recovery"

# Step 1: detect corruption
if docker exec "$APP_SERVICE" sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
  log "✅ Database appears healthy; exiting"
  exit 0
else
  log "❌ Corruption detected; proceeding with recovery"
fi

# Step 2: stop app
if [ -f "$COMPOSE_FILE" ]; then
  (cd "$REPO_DIR" && docker-compose -f "$COMPOSE_FILE" stop "$APP_SERVICE") || true
  sleep 5
fi

# Step 3: backup corrupted DB
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_COPY="/tmp/memory.db.corrupted_${TS}"
docker cp "$APP_SERVICE":"$DB_PATH" "$BACKUP_COPY" 2>/dev/null || true
log "Backup of corrupted DB: $BACKUP_COPY"

# Step 4: attempt sqlite .recover
log "Attempting SQLite .recover"
if docker exec "$APP_SERVICE" bash -c "sqlite3 $DB_PATH '.recover' | sqlite3 /app/data/memory_recovered.db"; then
  log "Recover command completed"
else
  log "⚠️  Recover command failed; will fall back to backup restore"
fi

# Step 5: verify recovered DB
if docker exec "$APP_SERVICE" sqlite3 /app/data/memory_recovered.db "PRAGMA integrity_check;" | grep -q "ok"; then
  log "✅ Recovered DB passed integrity check"
  docker exec "$APP_SERVICE" mv "$DB_PATH" "/app/data/memory.db.broken.${TS}" || true
  docker exec "$APP_SERVICE" mv /app/data/memory_recovered.db "$DB_PATH"
else
  log "❌ Recovered DB failed integrity; restoring from backup"
  LATEST_BACKUP=$(find /var/backups/mcp-monitoring/application -name 'app_*.tar.gz' -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2)
  [ -n "$LATEST_BACKUP" ] || fail "No application backups found"
  sudo "$REPO_DIR/scripts/restore_application.sh" "$LATEST_BACKUP"
fi

# Step 6: start app
if [ -f "$COMPOSE_FILE" ]; then
  (cd "$REPO_DIR" && docker-compose -f "$COMPOSE_FILE" start "$APP_SERVICE")
fi

log "Waiting for application health"
for i in $(seq 1 12); do
  if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
    log "✅ Application healthy"
    break
  fi
  log "...waiting ($i/12)"
  sleep 5
done

if ! curl -sf http://localhost:8080/health >/dev/null 2>&1; then
  fail "Application failed health check after recovery"
fi

log "================================================"
log "✅ DATABASE CORRUPTION RECOVERY COMPLETE"
log "================================================"

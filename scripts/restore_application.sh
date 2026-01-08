#!/bin/bash
# Application data restore (SQLite + ChromaDB + configs)

set -euo pipefail

BACKUP_DIR="/var/backups/mcp-monitoring/application"
LOG_FILE="/var/backups/mcp-monitoring/logs/application_restore.log"
APP_DATA_DIR="/var/mcp-data"
COMPOSE_FILE="docker-compose.yml"
APP_SERVICE="mcp-memory-server"
APP_USER="1000:1000"

mkdir -p "$(dirname "$LOG_FILE")" "$APP_DATA_DIR"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
fail() { log "❌ ERROR: $1"; exit 1; }

[ "$EUID" -eq 0 ] || fail "Run as root"
[ $# -ge 1 ] || fail "Usage: $0 <backup.tar.gz> | latest"
BACKUP_FILE="$1"
if [ "$BACKUP_FILE" = "latest" ]; then
  BACKUP_FILE=$(find "$BACKUP_DIR" -name "app_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2)
  [ -n "$BACKUP_FILE" ] || fail "No backups found"
  log "Using latest: $(basename "$BACKUP_FILE")"
fi
[ -f "$BACKUP_FILE" ] || fail "Backup not found: $BACKUP_FILE"

if [ -f "${BACKUP_FILE}.sha256" ]; then
  EXPECTED=$(cat "${BACKUP_FILE}.sha256")
  ACTUAL=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
  [ "$EXPECTED" = "$ACTUAL" ] || fail "Checksum mismatch"
  log "✅ Checksum verified"
fi

tar -tzf "$BACKUP_FILE" >/dev/null || fail "Archive corrupt"

TMPDIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TMPDIR"
EXTRACT_DIR=$(find "$TMPDIR" -mindepth 1 -maxdepth 1 -type d | head -1)
[ -n "$EXTRACT_DIR" ] || { rm -rf "$TMPDIR"; fail "No extracted directory"; }

if docker ps --format '{{.Names}}' | grep -q "^${APP_SERVICE}$"; then
  docker-compose -f "$COMPOSE_FILE" stop "$APP_SERVICE"
  sleep 5
fi

log "Backing up current state"
TS=$(date +%Y%m%d_%H%M%S)
[ -f "$APP_DATA_DIR/memory.db" ] && cp "$APP_DATA_DIR/memory.db" "$APP_DATA_DIR/memory.db.pre-restore_${TS}" || true
[ -d "$APP_DATA_DIR/chroma_db" ] && mv "$APP_DATA_DIR/chroma_db" "$APP_DATA_DIR/chroma_db.pre-restore_${TS}" || true

log "Restoring SQLite"
if [ -f "$EXTRACT_DIR/memory.db.gz" ]; then
  gunzip -c "$EXTRACT_DIR/memory.db.gz" > "$APP_DATA_DIR/memory.db"
else
  rm -rf "$TMPDIR"; fail "Database file missing"
fi

if sqlite3 "$APP_DATA_DIR/memory.db" "PRAGMA integrity_check;" | grep -q "ok"; then
  log "✅ DB integrity ok"
else
  rm -rf "$TMPDIR"; fail "DB integrity check failed"
fi

log "Restoring ChromaDB"
if [ -d "$EXTRACT_DIR/chroma_db" ]; then
  cp -r "$EXTRACT_DIR/chroma_db" "$APP_DATA_DIR/"
else
  log "⚠️  ChromaDB not found in backup"
fi

log "Restoring configs"
[ -f "$EXTRACT_DIR/config.yaml" ] && cp "$EXTRACT_DIR/config.yaml" "$APP_DATA_DIR/config.yaml"
[ -f "$EXTRACT_DIR/config.prod.yaml" ] && cp "$EXTRACT_DIR/config.prod.yaml" "$APP_DATA_DIR/config.prod.yaml"

chown -R "$APP_USER" "$APP_DATA_DIR"
chmod -R 755 "$APP_DATA_DIR"

rm -rf "$TMPDIR"

docker-compose -f "$COMPOSE_FILE" start "$APP_SERVICE"

log "Waiting for app health"
for i in $(seq 1 12); do
  if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
    log "✅ App healthy"
    break
  fi
  log "...waiting ($i/12)"
  sleep 5
done

if ! curl -sf http://localhost:8080/health >/dev/null 2>&1; then
  fail "App failed health check"
fi

TABLE_COUNT=$(docker exec "$APP_SERVICE" sqlite3 /app/data/memory.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo 0)
log "Tables present: $TABLE_COUNT"

log "================================================"
log "✅ APPLICATION RESTORE COMPLETE"
log "Backup: $(basename "$BACKUP_FILE")"
log "================================================"

if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  curl -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"✅ Application restored from $(basename "$BACKUP_FILE")\"}" >/dev/null 2>&1 || true
fi

exit 0

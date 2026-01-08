#!/bin/bash
# Grafana restore script (dashboards, datasources, optional DB)

set -euo pipefail

BACKUP_DIR="/var/backups/mcp-monitoring/grafana"
LOG_FILE="/var/backups/mcp-monitoring/logs/grafana_restore.log"
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
DOCKER_COMPOSE_FILE="docker-compose.monitoring.yml"
GRAFANA_CONTAINER="grafana"

mkdir -p "$(dirname "$LOG_FILE")"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
fail() { log "❌ ERROR: $1"; exit 1; }

[ $# -ge 1 ] || fail "Usage: $0 <backup.tar.gz> | latest"
BACKUP_FILE="$1"
if [ "$BACKUP_FILE" = "latest" ]; then
  BACKUP_FILE=$(find "$BACKUP_DIR" -name "grafana_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2)
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

if ! docker ps --format '{{.Names}}' | grep -q "^${GRAFANA_CONTAINER}$"; then
  docker-compose -f "$DOCKER_COMPOSE_FILE" start "$GRAFANA_CONTAINER"
  sleep 10
fi

for i in $(seq 1 30); do
  if curl -sf -u "$GRAFANA_USER:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

# Restore datasources
if [ -f "$EXTRACT_DIR/datasources.json" ]; then
  COUNT=$(jq '. | length' "$EXTRACT_DIR/datasources.json")
  log "Restoring $COUNT datasources"
  jq -c '.[]' "$EXTRACT_DIR/datasources.json" | while read -r ds; do
    NAME=$(echo "$ds" | jq -r '.name')
    BODY=$(echo "$ds" | jq 'del(.id, .uid)')
    RESP=$(curl -s -X POST -u "$GRAFANA_USER:$GRAFANA_PASSWORD" -H "Content-Type: application/json" "$GRAFANA_URL/api/datasources" -d "$BODY")
    if echo "$RESP" | jq -e '.id' >/dev/null 2>&1; then
      log "✅ Datasource restored: $NAME"
    else
      log "⚠️  Datasource may already exist: $NAME"
    fi
  done
fi

# Restore dashboards
DASH_COUNT=0
for f in $(find "$EXTRACT_DIR" -name 'dashboard_*.json' 2>/dev/null || true); do
  TITLE=$(jq -r '.dashboard.title // "Unknown"' "$f")
  BODY=$(jq '{dashboard: (.dashboard // . | del(.id, .uid, .version)), overwrite: true, message: "Restored from backup"}' "$f")
  RESP=$(curl -s -X POST -u "$GRAFANA_USER:$GRAFANA_PASSWORD" -H "Content-Type: application/json" "$GRAFANA_URL/api/dashboards/db" -d "$BODY")
  if echo "$RESP" | jq -e '.id' >/dev/null 2>&1; then
    ((DASH_COUNT++))
    log "✅ Dashboard restored: $TITLE"
  else
    MSG=$(echo "$RESP" | jq -r '.message // "unknown"')
    log "⚠️  Failed to restore $TITLE: $MSG"
  fi
done

# Optional DB restore
if [ -f "$EXTRACT_DIR/grafana.db.gz" ]; then
  read -r -p "Restore Grafana DB (overwrites everything)? [y/N]: " CONFIRM
  if [[ $CONFIRM =~ ^[Yy]$ ]]; then
    docker-compose -f "$DOCKER_COMPOSE_FILE" stop "$GRAFANA_CONTAINER"
    gunzip -c "$EXTRACT_DIR/grafana.db.gz" > /tmp/grafana.db
    docker cp /tmp/grafana.db "$GRAFANA_CONTAINER":/var/lib/grafana/grafana.db
    rm -f /tmp/grafana.db
    docker-compose -f "$DOCKER_COMPOSE_FILE" start "$GRAFANA_CONTAINER"
    sleep 10
    log "✅ Grafana DB restored"
  else
    log "Skipped DB restore"
  fi
fi

rm -rf "$TMPDIR"

log "================================================"
log "✅ GRAFANA RESTORE COMPLETE"
log "Dashboards restored: $DASH_COUNT"
log "Backup file: $(basename "$BACKUP_FILE")"
log "================================================"

if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  curl -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"✅ Grafana restored ($DASH_COUNT dashboards)\"}" >/dev/null 2>&1 || true
fi

exit 0

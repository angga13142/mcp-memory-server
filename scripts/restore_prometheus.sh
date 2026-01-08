#!/bin/bash
# Prometheus TSDB restore
# Usage: ./restore_prometheus.sh <backup.tar.gz> | latest

set -euo pipefail

BACKUP_DIR="/var/backups/mcp-monitoring/prometheus"
LOG_FILE="/var/backups/mcp-monitoring/logs/prometheus_restore.log"
PROMETHEUS_DATA_DIR="/var/mcp-data/prometheus"
DOCKER_COMPOSE_FILE="docker-compose.monitoring.yml"
PROM_CONTAINER="prometheus"
PROM_USER="65534:65534"  # nobody:nobody in prom image

mkdir -p "$(dirname "$LOG_FILE")" "$PROMETHEUS_DATA_DIR"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

fail() {
    log "❌ ERROR: $1"
    exit 1
}

[ "$EUID" -eq 0 ] || fail "Run as root"

[ $# -ge 1 ] || fail "Usage: $0 <backup.tar.gz> | latest"
BACKUP_FILE="$1"
if [ "$BACKUP_FILE" = "latest" ]; then
    BACKUP_FILE="$BACKUP_DIR/latest.tar.gz"
    log "Using latest backup"
fi
[ -f "$BACKUP_FILE" ] || fail "Backup not found: $BACKUP_FILE"

log "Backup: $BACKUP_FILE"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Size: $BACKUP_SIZE"

if [ -f "${BACKUP_FILE}.sha256" ]; then
    EXPECTED=$(cat "${BACKUP_FILE}.sha256")
    ACTUAL=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
    [ "$EXPECTED" = "$ACTUAL" ] || fail "Checksum mismatch"
    log "✅ Checksum verified"
else
    log "⚠️  No checksum file; skipping verification"
fi

tar -tzf "$BACKUP_FILE" >/dev/null || fail "Backup archive is corrupt"
log "✅ Archive integrity OK"

if docker ps --format '{{.Names}}' | grep -q "^${PROM_CONTAINER}$"; then
    log "Stopping Prometheus container"
    docker-compose -f "$DOCKER_COMPOSE_FILE" stop "$PROM_CONTAINER"
    sleep 5
fi

log "Backing up current data"
if [ -d "$PROMETHEUS_DATA_DIR" ]; then
    TS=$(date +%Y%m%d_%H%M%S)
    tar -czf "$BACKUP_DIR/pre-restore_${TS}.tar.gz" -C "$PROMETHEUS_DATA_DIR" . || log "⚠️  Could not back up current data"
fi

log "Extracting backup"
TMPDIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TMPDIR"
SNAPSHOT_DIR=$(find "$TMPDIR" -type d -name "snapshot_*" | head -1)
[ -n "$SNAPSHOT_DIR" ] || { rm -rf "$TMPDIR"; fail "Snapshot directory missing"; }

log "Restoring data"
rm -rf "$PROMETHEUS_DATA_DIR"/*
cp -r "$SNAPSHOT_DIR"/* "$PROMETHEUS_DATA_DIR/"
chown -R "$PROM_USER" "$PROMETHEUS_DATA_DIR"
rm -rf "$TMPDIR"

log "Starting Prometheus"
docker-compose -f "$DOCKER_COMPOSE_FILE" start "$PROM_CONTAINER"

log "Waiting for health"
for i in $(seq 1 12); do
    if curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1; then
        log "✅ Prometheus healthy"
        break
    fi
    log "...waiting ($i/12)"
    sleep 5
done

if ! curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1; then
    fail "Prometheus failed to start after restore"
fi

TS_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result | length' 2>/dev/null || echo 0)
log "Time series count: $TS_COUNT"

log "================================================"
log "✅ PROMETHEUS RESTORE COMPLETE"
log "Restored file: $(basename "$BACKUP_FILE")"
log "Data dir: $PROMETHEUS_DATA_DIR"
log "================================================"

if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ Prometheus restored from $(basename "$BACKUP_FILE")\"}" \
        >/dev/null 2>&1 || true
fi

exit 0

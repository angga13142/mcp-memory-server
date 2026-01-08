#!/bin/bash
# Quick Prometheus restore from latest backup (minimal checks)

set -euo pipefail

BACKUP_FILE="/var/backups/mcp-monitoring/prometheus/latest.tar.gz"
PROM_DATA_DIR="/var/mcp-data/prometheus"
DOCKER_COMPOSE_FILE="docker-compose.monitoring.yml"
PROM_CONTAINER="prometheus"
PROM_USER="65534:65534"

echo "⚡ QUICK PROMETHEUS RESTORE"
echo "This will replace current Prometheus data. Ctrl+C to abort."
read -r

[ -f "$BACKUP_FILE" ] || { echo "❌ No backup found at $BACKUP_FILE"; exit 1; }

if docker ps --format '{{.Names}}' | grep -q "^${PROM_CONTAINER}$"; then
  docker-compose -f "$DOCKER_COMPOSE_FILE" stop "$PROM_CONTAINER"
  sleep 3
fi

TMPDIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TMPDIR"
SNAPSHOT_DIR=$(find "$TMPDIR" -type d -name "snapshot_*" | head -1)
[ -n "$SNAPSHOT_DIR" ] || { echo "❌ Snapshot dir missing"; rm -rf "$TMPDIR"; exit 1; }

rm -rf "$PROM_DATA_DIR"/*
cp -r "$SNAPSHOT_DIR"/* "$PROM_DATA_DIR/"
chown -R "$PROM_USER" "$PROM_DATA_DIR"
rm -rf "$TMPDIR"

docker-compose -f "$DOCKER_COMPOSE_FILE" start "$PROM_CONTAINER"

echo "✅ Quick restore done. Check: curl http://localhost:9090/-/healthy"

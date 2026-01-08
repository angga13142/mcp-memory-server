#!/bin/bash
#
# Restore Prometheus from Backup
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mcp-monitoring/prometheus}"
PROMETHEUS_DATA_DIR="${PROMETHEUS_DATA_DIR:-/var/lib/prometheus}"
BACKUP_FILE="${1:-latest}"

# Logging
LOG_FILE="/var/log/mcp-backups/prometheus-restore.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $*"
    exit 1
}

log "Starting Prometheus restore..."

# Determine backup file
if [ "$BACKUP_FILE" = "latest" ]; then
    BACKUP_FILE="${BACKUP_DIR}/latest.tar.gz"
elif [ ! -f "$BACKUP_FILE" ]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
fi

log "Using backup: $BACKUP_FILE"

# Verify checksum
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
    log "Verifying checksum..."
    cd "$(dirname "$BACKUP_FILE")"
    if ! sha256sum -c "$(basename "$CHECKSUM_FILE")"; then
        error "Checksum verification failed"
    fi
    log "Checksum verified"
fi

# Stop Prometheus
log "Stopping Prometheus..."
docker-compose -f docker-compose.monitoring.yml stop prometheus || true
sleep 5

# Backup current data
log "Backing up current Prometheus data..."
if [ -d "$PROMETHEUS_DATA_DIR" ]; then
    CURRENT_BACKUP="${PROMETHEUS_DATA_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    mv "$PROMETHEUS_DATA_DIR" "$CURRENT_BACKUP"
    log "Current data backed up to: $CURRENT_BACKUP"
fi

# Extract backup
log "Extracting backup..."
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find snapshot directory
SNAPSHOT_DIR=$(find "$TEMP_DIR" -type d -name "snapshot_*" | head -1)

if [ -z "$SNAPSHOT_DIR" ]; then
    error "Snapshot directory not found in backup"
fi

log "Found snapshot: $SNAPSHOT_DIR"

# Restore data
log "Restoring data..."
mkdir -p "$PROMETHEUS_DATA_DIR"
cp -r "$SNAPSHOT_DIR"/* "$PROMETHEUS_DATA_DIR/"

# Set permissions
log "Setting permissions..."
chown -R 65534:65534 "$PROMETHEUS_DATA_DIR"

# Cleanup
rm -rf "$TEMP_DIR"

# Start Prometheus
log "Starting Prometheus..."
docker-compose -f docker-compose.monitoring.yml start prometheus

# Wait for Prometheus to be ready
log "Waiting for Prometheus to start..."
for i in {1..30}; do
    if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log "✅ Prometheus is healthy"
        break
    fi
    sleep 2
done

# Verify data
log "Verifying restored data..."
DATA_POINTS=$(curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result | length')
log "Found $DATA_POINTS time series"

log "Restore completed successfully"
exit 0
